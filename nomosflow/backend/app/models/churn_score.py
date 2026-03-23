import uuid
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class ChurnScore(Base):
    __tablename__ = "churn_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)
    reasoning = Column(Text, nullable=True)
    factors = Column(JSONB, nullable=True)
    action_suggested = Column(Text, nullable=True)
    scored_at = Column(DateTime, default=func.now())

    customer = relationship("Customer", back_populates="churn_scores")
