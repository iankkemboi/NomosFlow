from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models.customer import Customer
from app.models.partner import Partner
from app.models.payment import Payment
from app.models.churn_score import ChurnScore
from app.schemas.customer import CustomerResponse, CustomerCreate, CustomerUpdate, CustomerFullProfile



router = APIRouter()


@router.get("", response_model=List[CustomerResponse])
def list_customers(
    partner_id: Optional[UUID] = Query(None),
    device_type: Optional[str] = Query(None),
    contract_status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Customer)
    if partner_id:
        query = query.filter(Customer.partner_id == partner_id)
    if device_type:
        query = query.filter(Customer.device_type == device_type)
    if contract_status:
        query = query.filter(Customer.contract_status == contract_status)
    if risk_level:
        # Only match customers whose LATEST churn score has the requested risk level
        latest_per_customer = (
            db.query(
                ChurnScore.customer_id,
                func.max(ChurnScore.scored_at).label("max_scored_at"),
            )
            .group_by(ChurnScore.customer_id)
            .subquery()
        )
        subq = (
            db.query(ChurnScore.customer_id)
            .join(
                latest_per_customer,
                (ChurnScore.customer_id == latest_per_customer.c.customer_id)
                & (ChurnScore.scored_at == latest_per_customer.c.max_scored_at),
            )
            .filter(ChurnScore.risk_level == risk_level)
            .subquery()
        )
        query = query.filter(Customer.id.in_(subq))
    return query.order_by(Customer.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: UUID, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/{customer_id}/full-profile", response_model=CustomerFullProfile)
def get_full_profile(customer_id: UUID, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    partner = db.query(Partner).filter(Partner.id == customer.partner_id).first()
    latest_score = (
        db.query(ChurnScore)
        .filter(ChurnScore.customer_id == customer_id)
        .order_by(ChurnScore.scored_at.desc())
        .first()
    )
    failed_count = db.query(func.count(Payment.id)).filter(
        Payment.customer_id == customer_id,
        Payment.status.in_(["failed", "retrying", "written_off"]),
    ).scalar()
    total_count = db.query(func.count(Payment.id)).filter(Payment.customer_id == customer_id).scalar()

    profile = CustomerFullProfile.model_validate(customer)
    profile.partner_name = partner.name if partner else None
    profile.latest_churn_score = latest_score.score if latest_score else None
    profile.latest_risk_level = latest_score.risk_level if latest_score else None
    profile.failed_payments_count = failed_count or 0
    profile.total_payments_count = total_count or 0
    return profile


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(body: CustomerCreate, db: Session = Depends(get_db)):
    customer = Customer(**body.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: UUID, body: CustomerUpdate, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer
