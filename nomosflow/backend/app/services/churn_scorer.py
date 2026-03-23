from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.churn_score import ChurnScore
from app.models.dunning_action import DunningAction
from app.services.gemini_service import score_churn_risk


def build_customer_context(customer: Customer) -> dict:
    return {
        "name": customer.name,
        "device_type": customer.device_type,
        "tariff_type": customer.tariff_type,
        "contract_start": str(customer.contract_start),
        "contract_status": customer.contract_status,
        "city": customer.city,
        "annual_saving_eur": float(customer.annual_saving_eur or 0),
        "salary_day": customer.salary_day,
    }


def build_payment_history(payments: list) -> list:
    history = []
    for p in payments:
        history.append({
            "status": p.status,
            "amount_eur": float(p.amount_eur),
            "due_date": str(p.due_date),
            "paid_at": str(p.paid_at) if p.paid_at else None,
            "failure_reason": p.failure_reason,
            "retry_count": p.retry_count,
        })
    return history


def score_customer(customer_id: str, db: Session) -> ChurnScore:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise ValueError(f"Customer {customer_id} not found")

    payments = (
        db.query(Payment)
        .filter(Payment.customer_id == customer_id)
        .order_by(Payment.due_date.desc())
        .limit(6)
        .all()
    )
    dunning_actions = (
        db.query(DunningAction)
        .filter(DunningAction.customer_id == customer_id)
        .all()
    )

    customer_ctx = build_customer_context(customer)
    payment_history = build_payment_history(payments)
    dunning_list = [{"action_type": d.action_type, "outcome": d.outcome} for d in dunning_actions]

    result = score_churn_risk(customer_ctx, payment_history, dunning_list)

    churn_score = ChurnScore(
        customer_id=customer_id,
        score=max(0, min(100, int(result["score"]))),
        risk_level=result["risk_level"],
        reasoning=result.get("reasoning"),
        factors=result.get("factors"),
        action_suggested=result.get("action_suggested"),
    )
    db.add(churn_score)
    db.commit()
    db.refresh(churn_score)
    return churn_score


def simple_score_customer(customer: Customer, db: Session) -> ChurnScore:
    """Heuristic-based scoring without Gemini (fast fallback)."""
    payments = (
        db.query(Payment)
        .filter(Payment.customer_id == customer.id)
        .order_by(Payment.due_date.desc())
        .limit(6)
        .all()
    )

    failed_count = sum(1 for p in payments if p.status in ("failed", "retrying"))
    total_count = len(payments)
    contract_age_days = (date.today() - customer.contract_start).days

    score = 0
    if total_count > 0:
        fail_rate = failed_count / total_count
        score += int(fail_rate * 50)

    if contract_age_days < 60:
        score += 15
    elif contract_age_days < 180:
        score += 5

    if customer.contract_status == "suspended":
        score += 25
    elif customer.contract_status == "cancelled":
        score = 100

    exhausted = [p for p in payments if p.retry_count >= p.max_retries]
    if exhausted:
        score += 20

    score = min(score, 100)

    if score <= 25:
        risk_level = "low"
    elif score <= 50:
        risk_level = "medium"
    elif score <= 75:
        risk_level = "high"
    else:
        risk_level = "critical"

    churn_score = ChurnScore(
        customer_id=customer.id,
        score=score,
        risk_level=risk_level,
        reasoning=f"Heuristic: {failed_count} failed out of {total_count} recent payments, contract age {contract_age_days}d.",
        factors={
            "failed_payments_30d": failed_count,
            "contract_age_days": contract_age_days,
            "device_type": customer.device_type,
            "is_dynamic_tariff": customer.tariff_type == "dynamic",
        },
        action_suggested="Review payment history and contact customer directly." if score > 50 else "Monitor only.",
    )
    db.add(churn_score)
    db.commit()
    db.refresh(churn_score)
    return churn_score
