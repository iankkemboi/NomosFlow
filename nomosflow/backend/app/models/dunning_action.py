import uuid
from sqlalchemy import Column, String, DateTime, Date, Numeric, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class DunningAction(Base):
    __tablename__ = "dunning_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(50), nullable=False)
    ai_generated_message = Column(Text, nullable=True)
    ai_failure_reason = Column(String(100), nullable=True)
    ai_confidence = Column(Numeric(4, 3), nullable=True)
    retry_scheduled_for = Column(Date, nullable=True)
    triggered_by = Column(String(50), default="system")
    outcome = Column(String(50), nullable=True)
    executed_at = Column(DateTime, default=func.now())

    payment = relationship("Payment", back_populates="dunning_actions")
    customer = relationship("Customer", back_populates="dunning_actions")
