from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class ChurnScoreBase(BaseModel):
    score: int
    risk_level: str
    reasoning: Optional[str] = None
    factors: Optional[Any] = None
    action_suggested: Optional[str] = None


class ChurnScoreCreate(ChurnScoreBase):
    customer_id: UUID


class ChurnScoreResponse(ChurnScoreBase):
    id: UUID
    customer_id: UUID
    scored_at: datetime

    class Config:
        from_attributes = True


class ChurnScoreWithCustomer(ChurnScoreResponse):
    customer_name: Optional[str] = None
    partner_name: Optional[str] = None
    device_type: Optional[str] = None
    contract_status: Optional[str] = None
