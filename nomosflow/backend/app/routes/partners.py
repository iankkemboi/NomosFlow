from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.partner import Partner
from app.models.customer import Customer
from app.schemas.partner import PartnerResponse, PartnerCreate

router = APIRouter()


@router.get("", response_model=List[PartnerResponse])
def list_partners(db: Session = Depends(get_db)):
    partners = db.query(Partner).all()
    result = []
    for p in partners:
        count = db.query(func.count(Customer.id)).filter(Customer.partner_id == p.id).scalar()
        data = PartnerResponse.model_validate(p)
        data.customer_count = count
        result.append(data)
    return result


@router.get("/{partner_id}", response_model=PartnerResponse)
def get_partner(partner_id: UUID, db: Session = Depends(get_db)):
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    count = db.query(func.count(Customer.id)).filter(Customer.partner_id == partner.id).scalar()
    data = PartnerResponse.model_validate(partner)
    data.customer_count = count
    return data


@router.post("", response_model=PartnerResponse, status_code=201)
def create_partner(body: PartnerCreate, db: Session = Depends(get_db)):
    partner = Partner(**body.model_dump())
    db.add(partner)
    db.commit()
    db.refresh(partner)
    data = PartnerResponse.model_validate(partner)
    data.customer_count = 0
    return data
