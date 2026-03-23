from uuid import UUID
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
from decimal import Decimal


class CustomerBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    tariff_type: str = "dynamic"
    device_type: str
    monthly_kwh: Optional[Decimal] = None
    annual_saving_eur: Optional[Decimal] = None
    salary_day: Optional[int] = None
    contract_start: date
    contract_status: str = "active"
    city: Optional[str] = None


class CustomerCreate(CustomerBase):
    partner_id: UUID


class CustomerUpdate(BaseModel):
    contract_status: Optional[str] = None
    tariff_type: Optional[str] = None
    monthly_kwh: Optional[Decimal] = None
    annual_saving_eur: Optional[Decimal] = None


class CustomerResponse(CustomerBase):
    id: UUID
    partner_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerFullProfile(CustomerResponse):
    partner_name: Optional[str] = None
    latest_churn_score: Optional[int] = None
    latest_risk_level: Optional[str] = None
    failed_payments_count: int = 0
    total_payments_count: int = 0
