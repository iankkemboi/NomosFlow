from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PartnerBase(BaseModel):
    name: str
    slug: str
    device_type: str
    brand_color: Optional[str] = "#3D6B2C"
    logo_url: Optional[str] = None


class PartnerCreate(PartnerBase):
    pass


class PartnerResponse(PartnerBase):
    id: UUID
    created_at: datetime
    customer_count: Optional[int] = 0

    class Config:
        from_attributes = True
