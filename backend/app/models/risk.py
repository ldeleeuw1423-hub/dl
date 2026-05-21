import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, Integer, ForeignKey, text, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Risk(Base):
    __tablename__ = "risks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    probability = Column(Integer, nullable=False)
    impact = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False, default=0)
    owner = Column(String(255), nullable=True)
    mitigation_measure = Column(Text, nullable=True)
    deadline = Column(Date, nullable=True)
    status = Column(String(50), nullable=False, default="open")
    residual_risk = Column(Integer, nullable=True)
    auto_detected = Column(Boolean, nullable=False, default=False)
    source = Column(String(50), nullable=False, default="manual")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="risks")


@event.listens_for(Risk, "before_insert")
@event.listens_for(Risk, "before_update")
def calculate_score(mapper, connection, target):
    target.score = target.probability * target.impact
