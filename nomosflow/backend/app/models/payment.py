import uuid
from sqlalchemy import Column, String, DateTime, Date, Integer, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    amount_eur = Column(Numeric(10, 2), nullable=False)
    period_month = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    failure_reason = Column(String(100), nullable=True)
    failure_classified_by = Column(String(20), default="manual")
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=func.now())

    customer = relationship("Customer", back_populates="payments")
    dunning_actions = relationship("DunningAction", back_populates="payment", cascade="all, delete-orphan")
