import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Partner(Base):
    __tablename__ = "partners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    device_type = Column(String(50), nullable=False)
    brand_color = Column(String(7), default="#3D6B2C")
    logo_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    customers = relationship("Customer", back_populates="partner", cascade="all, delete-orphan")
