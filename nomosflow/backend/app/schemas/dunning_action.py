from uuid import UUID
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
from decimal import Decimal


class DunningActionBase(BaseModel):
    action_type: str
    ai_generated_message: Optional[str] = None
    ai_failure_reason: Optional[str] = None
    ai_confidence: Optional[Decimal] = None
    retry_scheduled_for: Optional[date] = None
    triggered_by: str = "system"
    outcome: Optional[str] = None


class DunningActionCreate(DunningActionBase):
    payment_id: UUID
    customer_id: UUID


class DunningActionResponse(DunningActionBase):
    id: UUID
    payment_id: UUID
    customer_id: UUID
    executed_at: datetime

    class Config:
        from_attributes = True


class DunningQueueItem(BaseModel):
    payment_id: str
    customer_id: str
    customer_name: str
    device_type: str
    amount_eur: float
    status: str
    failure_reason: Optional[str] = None
    retry_count: int
    max_retries: int
    next_retry_date: Optional[str] = None
    due_date: str
    dunning_stage: str
