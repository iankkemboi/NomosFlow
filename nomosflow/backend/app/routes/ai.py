from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.churn_score import ChurnScore
from app.services.gemini_service import classify_payment_failure
from app.services.churn_scorer import build_customer_context
from app.services.message_generator import generate_for_customer
from app.services.gemini_quota import quota_status, GeminiQuotaExceededError

router = APIRouter()


class ClassifyRequest(BaseModel):
    customer_id: UUID
    payment_id: UUID


class RetentionMessageRequest(BaseModel):
    customer_id: UUID
    payment_id: Optional[UUID] = None


@router.post("/classify-failure")
def classify_failure(body: ClassifyRequest, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == body.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    payment = db.query(Payment).filter(Payment.id == body.payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    recent_payments = (
        db.query(Payment)
        .filter(Payment.customer_id == customer.id)
        .order_by(Payment.due_date.desc())
        .limit(6)
        .all()
    )
    succeeded = sum(1 for p in recent_payments if p.status == "paid")
    failed_count = len(recent_payments) - succeeded

    customer_ctx = build_customer_context(customer)
    customer_ctx["contract_age_days"] = (date.today() - customer.contract_start).days
    customer_ctx["payment_history_summary"] = (
        f"{succeeded} of last {len(recent_payments)} payments succeeded, {failed_count} failed"
    )

    payment_ctx = {
        "amount_eur": float(payment.amount_eur),
        "day_of_month_failed": payment.due_date.day if payment.due_date else date.today().day,
        "retry_count": payment.retry_count,
    }

    result = classify_payment_failure(customer_ctx, payment_ctx)

    payment.failure_reason = result.get("failure_reason")
    payment.failure_classified_by = "ai"
    db.commit()

    return result


@router.post("/retention-message")
def get_retention_message(body: RetentionMessageRequest, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == body.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    try:
        return generate_for_customer(str(body.customer_id), db)
    except GeminiQuotaExceededError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard-summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_customers = db.query(func.count(Customer.id)).scalar()
    failed_payments = db.query(func.count(Payment.id)).filter(
        Payment.status.in_(["failed", "retrying"])
    ).scalar()
    # Only count customers whose LATEST churn score is high/critical
    latest_per_customer = (
        db.query(
            ChurnScore.customer_id,
            func.max(ChurnScore.scored_at).label("max_scored_at"),
        )
        .group_by(ChurnScore.customer_id)
        .subquery()
    )
    at_risk = (
        db.query(func.count(ChurnScore.customer_id))
        .join(
            latest_per_customer,
            (ChurnScore.customer_id == latest_per_customer.c.customer_id)
            & (ChurnScore.scored_at == latest_per_customer.c.max_scored_at),
        )
        .filter(ChurnScore.risk_level.in_(["high", "critical"]))
        .scalar()
    )
    revenue_at_risk = db.query(func.sum(Payment.amount_eur)).filter(
        Payment.status.in_(["failed", "retrying"])
    ).scalar() or 0

    return {
        "total_customers": total_customers,
        "failed_payments": failed_payments,
        "at_risk_customers": at_risk,
        "revenue_at_risk_eur": float(revenue_at_risk),
    }


@router.get("/quota-status")
def get_quota_status():
    """Current Gemini quota usage for the active window."""
    return quota_status()
