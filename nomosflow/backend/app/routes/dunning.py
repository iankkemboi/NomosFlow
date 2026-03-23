from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models.dunning_action import DunningAction
from app.models.payment import Payment
from app.models.customer import Customer
from app.schemas.dunning_action import DunningActionResponse, DunningQueueItem
from app.services.dunning_engine import run_dunning_cycle
from app.services.retry_scheduler import get_dunning_stage
from app.services.gemini_quota import quota_status

router = APIRouter()


@router.post("/run-cycle")
def trigger_dunning_cycle(
    partner_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    results = run_dunning_cycle(db, partner_id=str(partner_id) if partner_id else None, limit=limit)
    remaining = db.query(Payment).filter(Payment.status.in_(["failed", "retrying"])).count()
    response = {"status": "completed", "queue_remaining": remaining, **results}
    if results.get("fallback_count", 0) > 0:
        response["quota"] = quota_status()
    return response


@router.get("/timeline/{customer_id}", response_model=List[DunningActionResponse])
def get_dunning_timeline(customer_id: UUID, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    actions = (
        db.query(DunningAction)
        .filter(DunningAction.customer_id == customer_id)
        .order_by(DunningAction.executed_at.asc())
        .all()
    )
    return actions


@router.get("/queue", response_model=List[DunningQueueItem])
def get_dunning_queue(db: Session = Depends(get_db)):
    rows = (
        db.query(Payment, Customer)
        .join(Customer, Payment.customer_id == Customer.id)
        .filter(Payment.status.in_(["failed", "retrying"]))
        .order_by(Payment.created_at.desc())
        .all()
    )
    result = []
    for payment, customer in rows:
        result.append(DunningQueueItem(
            payment_id=str(payment.id),
            customer_id=str(customer.id),
            customer_name=customer.name,
            device_type=customer.device_type,
            amount_eur=float(payment.amount_eur),
            status=payment.status,
            failure_reason=payment.failure_reason,
            retry_count=payment.retry_count,
            max_retries=payment.max_retries,
            next_retry_date=str(payment.next_retry_date) if payment.next_retry_date else None,
            due_date=str(payment.due_date),
            dunning_stage=get_dunning_stage(payment.retry_count, payment.failure_reason or "unknown"),
        ))
    return result
