import uuid
from sqlalchemy import Column, String, DateTime, Date, Integer, Numeric, ForeignKey, func, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    tariff_type = Column(String(50), nullable=False, default="dynamic")
    device_type = Column(String(50), nullable=False)
    monthly_kwh = Column(Numeric(10, 2), nullable=True)
    annual_saving_eur = Column(Numeric(10, 2), nullable=True)
    salary_day = Column(Integer, nullable=True)
    contract_start = Column(Date, nullable=False)
    contract_status = Column(String(50), nullable=False, default="active")
    city = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now())

    partner = relationship("Partner", back_populates="customers")
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")
    dunning_actions = relationship("DunningAction", back_populates="customer", cascade="all, delete-orphan")
    churn_scores = relationship("ChurnScore", back_populates="customer", cascade="all, delete-orphan")
