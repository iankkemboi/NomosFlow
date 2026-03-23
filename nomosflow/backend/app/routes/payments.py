from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.database import get_db
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.partner import Partner
from app.schemas.payment import PaymentResponse, PaymentCreate, PaymentFailRequest, PaymentWithCustomer

router = APIRouter()


@router.get("", response_model=List[PaymentWithCustomer])
def list_payments(
    status: Optional[str] = Query(None),
    partner_id: Optional[UUID] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Payment, Customer, Partner).join(
        Customer, Payment.customer_id == Customer.id
    ).join(
        Partner, Customer.partner_id == Partner.id
    )
    if status:
        query = query.filter(Payment.status == status)
    if partner_id:
        query = query.filter(Customer.partner_id == partner_id)

    rows = query.order_by(Payment.created_at.desc()).limit(limit).all()
    result = []
    for payment, customer, partner in rows:
        data = PaymentWithCustomer.model_validate(payment)
        data.customer_name = customer.name
        data.partner_name = partner.name
        data.device_type = customer.device_type
        result.append(data)
    return result


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: UUID, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.get("/customer/{customer_id}", response_model=List[PaymentResponse])
def get_customer_payments(customer_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(Payment)
        .filter(Payment.customer_id == customer_id)
        .order_by(Payment.due_date.desc())
        .all()
    )


@router.post("/fail", response_model=PaymentResponse, status_code=201)
def create_failed_payment(body: PaymentFailRequest, db: Session = Depends(get_db)):
    """Seed helper: create a failed payment for a customer."""
    customer = db.query(Customer).filter(Customer.id == body.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    today = date.today()
    payment = Payment(
        customer_id=body.customer_id,
        amount_eur=body.amount_eur,
        period_month=today.replace(day=1),
        due_date=today,
        status="failed",
        failure_reason=body.failure_reason,
        retry_count=0,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
