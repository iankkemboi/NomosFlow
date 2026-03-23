from uuid import UUID
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
from decimal import Decimal


class PaymentBase(BaseModel):
    amount_eur: Decimal
    period_month: date
    due_date: date
    status: str = "pending"
    failure_reason: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    next_retry_date: Optional[date] = None


class PaymentCreate(PaymentBase):
    customer_id: UUID


class PaymentFailRequest(BaseModel):
    customer_id: UUID
    amount_eur: Decimal
    failure_reason: Optional[str] = "unknown"


class PaymentResponse(PaymentBase):
    id: UUID
    customer_id: UUID
    paid_at: Optional[datetime] = None
    failure_classified_by: Optional[str] = "manual"
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentWithCustomer(PaymentResponse):
    customer_name: Optional[str] = None
    partner_name: Optional[str] = None
    device_type: Optional[str] = None
