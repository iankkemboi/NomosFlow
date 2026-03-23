from datetime import date
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.dunning_action import DunningAction
from app.services.gemini_service import classify_payment_failure
from app.services.gemini_quota import GeminiQuotaExceededError
from app.services.retry_scheduler import calculate_next_retry, classify_failure_reason_rules

try:
    from google.api_core.exceptions import ResourceExhausted as _GeminiAPIQuotaError
except ImportError:
    _GeminiAPIQuotaError = None

AI_TIMEOUT_SECONDS = 20
AI_MAX_WORKERS = 5  # keep below Gemini concurrent request limits


def _build_context(payment: Payment, db: Session) -> Optional[dict]:
    """Serial DB read — builds all context needed for AI classify. No writes."""
    customer = db.query(Customer).filter(Customer.id == payment.customer_id).first()
    if not customer:
        return None

    recent = (
        db.query(Payment)
        .filter(Payment.customer_id == customer.id)
        .order_by(Payment.due_date.desc())
        .limit(6)
        .all()
    )
    total = len(recent)
    succeeded = sum(1 for p in recent if p.status == "paid")
    failed_count = total - succeeded

    customer_ctx = {
        "name": customer.name,
        "device_type": customer.device_type,
        "tariff_type": customer.tariff_type,
        "contract_start": str(customer.contract_start),
        "contract_status": customer.contract_status,
        "city": customer.city or "",
        "annual_saving_eur": float(customer.annual_saving_eur or 0),
        "contract_age_days": (date.today() - customer.contract_start).days,
        "payment_history_summary": f"{succeeded} of last {total} payments succeeded, {failed_count} failed",
        "salary_day": customer.salary_day,
    }
    payment_ctx = {
        "amount_eur": float(payment.amount_eur),
        "day_of_month_failed": payment.due_date.day if payment.due_date else date.today().day,
        "retry_count": payment.retry_count,
    }
    return {
        "payment_id": str(payment.id),
        "payment": payment,
        "customer": customer,
        "customer_ctx": customer_ctx,
        "payment_ctx": payment_ctx,
    }


def _ai_classify(item: dict) -> dict:
    """Pure I/O — no DB. Safe to run in a thread."""
    try:
        result = classify_payment_failure(item["customer_ctx"], item["payment_ctx"])
        return {**item, "classification": result, "ai_error": None}
    except GeminiQuotaExceededError:
        # Our internal daily cap — fall back to rules, tag so caller can count it
        return {**item, "classification": None, "ai_error": "quota_exceeded"}
    except Exception as e:
        # Google SDK quota error (429 from the API itself)
        if _GeminiAPIQuotaError and isinstance(e, _GeminiAPIQuotaError):
            return {**item, "classification": None, "ai_error": "quota_exceeded"}
        return {**item, "classification": None, "ai_error": str(e)}


def _apply_writes(result: dict, db: Session) -> list:
    """Apply all DB mutations for one payment. Called serially from main thread."""
    actions = []
    payment: Payment = db.merge(result["payment"])
    customer: Customer = db.merge(result["customer"])
    customer_ctx: dict = result["customer_ctx"]

    classification = result.get("classification")
    if classification:
        failure_reason = classification.get("failure_reason", "unknown")
        confidence = classification.get("confidence", 0.5)
        explanation = classification.get("explanation", "")
        classified_by = "ai"
    else:
        # Fallback to rules if AI timed out or failed
        fb = classify_failure_reason_rules(
            retry_count=payment.retry_count,
            contract_age_days=customer_ctx["contract_age_days"],
            salary_day=customer_ctx["salary_day"],
            day_of_month_failed=result["payment_ctx"]["day_of_month_failed"],
            existing_reason=payment.failure_reason,
        )
        failure_reason = fb["failure_reason"]
        confidence = fb["confidence"]
        explanation = f"Rule-based fallback (AI unavailable): {result.get('ai_error', '')}"
        classified_by = "rules"

    payment.failure_reason = failure_reason
    payment.failure_classified_by = classified_by
    db.add(DunningAction(
        payment_id=payment.id,
        customer_id=customer.id,
        action_type="ai_classify",
        ai_failure_reason=failure_reason,
        ai_confidence=confidence,
        ai_generated_message=explanation,
        triggered_by="system",
        outcome="success",
    ))
    actions.append({"type": "classified", "reason": failure_reason, "confidence": confidence, "by": classified_by})

    if payment.retry_count < payment.max_retries:
        next_retry = calculate_next_retry(
            failure_reason=failure_reason,
            retry_count=payment.retry_count,
            salary_day=customer.salary_day,
            failed_date=payment.due_date,
        )
        payment.next_retry_date = next_retry
        payment.status = "retrying"
        db.add(DunningAction(
            payment_id=payment.id,
            customer_id=customer.id,
            action_type="retry_scheduled",
            retry_scheduled_for=next_retry,
            triggered_by="system",
            outcome="pending",
        ))
        actions.append({"type": "retry_scheduled", "date": str(next_retry)})
        payment.retry_count += 1
    else:
        payment.status = "written_off"
        if customer.contract_status == "active":
            customer.contract_status = "suspended"
        db.add(DunningAction(
            payment_id=payment.id,
            customer_id=customer.id,
            action_type="suspended",
            triggered_by="system",
            outcome="pending",
        ))
        actions.append({"type": "suspended"})

    return actions


def run_dunning_cycle(db: Session, partner_id: str = None, limit: int = 50) -> dict:
    """
    Parallel AI dunning cycle:
      Phase 1 — Serial DB reads: build context for all payments
      Phase 2 — Parallel AI: fan out classify_payment_failure calls (no DB)
      Phase 3 — Serial DB writes: apply results, fallback to rules on AI failure
    """
    query = db.query(Payment).filter(Payment.status.in_(["failed", "retrying"]))
    if partner_id:
        query = query.join(Customer).filter(Customer.partner_id == partner_id)
    failed_payments = query.order_by(Payment.created_at.asc()).limit(limit).all()

    # Phase 1: build all contexts from DB
    items, skipped = [], []
    for payment in failed_payments:
        ctx = _build_context(payment, db)
        if ctx:
            items.append(ctx)
        else:
            skipped.append(str(payment.id))

    # Phase 2: fan out AI calls in parallel
    ai_results = []
    if items:
        with ThreadPoolExecutor(max_workers=min(AI_MAX_WORKERS, len(items))) as pool:
            future_map = {pool.submit(_ai_classify, item): item for item in items}
            try:
                for future in as_completed(future_map, timeout=AI_TIMEOUT_SECONDS + 5):
                    try:
                        ai_results.append(future.result(timeout=AI_TIMEOUT_SECONDS))
                    except (FuturesTimeout, Exception) as e:
                        orig = future_map[future]
                        ai_results.append({**orig, "classification": None, "ai_error": str(e)})
            except FuturesTimeout:
                # Some futures still running — collect what finished, fallback the rest
                for future, orig in future_map.items():
                    if future.done():
                        try:
                            if not any(r.get("payment_id") == orig["payment_id"] for r in ai_results):
                                ai_results.append(future.result())
                        except Exception as e:
                            ai_results.append({**orig, "classification": None, "ai_error": str(e)})
                    else:
                        future.cancel()
                        ai_results.append({**orig, "classification": None, "ai_error": "timeout"})

    # Phase 3: apply DB writes serially
    results = {"processed": 0, "fallback_count": 0, "actions": [], "errors": []}
    for result in ai_results:
        try:
            if result.get("ai_error"):
                results["fallback_count"] += 1
            actions = _apply_writes(result, db)
            results["processed"] += 1
            results["actions"].extend(actions)
        except Exception as e:
            results["errors"].append({"payment_id": result.get("payment_id"), "error": str(e)})

    if ai_results:
        db.commit()

    for pid in skipped:
        results["errors"].append({"payment_id": pid, "error": "customer not found"})

    return results
