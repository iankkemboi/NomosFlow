from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.churn_score import ChurnScore
from app.services.gemini_service import generate_retention_message
from app.services.churn_scorer import build_customer_context


def generate_for_customer(customer_id: str, db: Session) -> dict:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise ValueError(f"Customer {customer_id} not found")

    latest_payment = (
        db.query(Payment)
        .filter(Payment.customer_id == customer_id)
        .filter(Payment.status.in_(["failed", "retrying", "written_off"]))
        .order_by(Payment.due_date.desc())
        .first()
    )

    latest_churn = (
        db.query(ChurnScore)
        .filter(ChurnScore.customer_id == customer_id)
        .order_by(ChurnScore.scored_at.desc())
        .first()
    )

    customer_ctx = build_customer_context(customer)
    payment_ctx = {
        "amount_eur": float(latest_payment.amount_eur) if latest_payment else 0,
        "failure_reason": latest_payment.failure_reason if latest_payment else "unknown",
        "retry_count": latest_payment.retry_count if latest_payment else 0,
    }
    churn_ctx = {
        "score": latest_churn.score if latest_churn else 50,
        "risk_level": latest_churn.risk_level if latest_churn else "medium",
    }

    return generate_retention_message(customer_ctx, payment_ctx, churn_ctx)
