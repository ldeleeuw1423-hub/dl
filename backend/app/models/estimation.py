import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Numeric, Integer, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Estimation(Base):
    __tablename__ = "estimations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    discipline = Column(String(50), nullable=True)
    hours_engineering = Column(Numeric(10, 2), nullable=True)
    hours_pm = Column(Numeric(10, 2), nullable=True)
    hours_om = Column(Numeric(10, 2), nullable=True)
    hours_workprep = Column(Numeric(10, 2), nullable=True)
    hours_execution = Column(Numeric(10, 2), nullable=True)
    cost_materials = Column(Numeric(14, 2), nullable=True)
    cost_total = Column(Numeric(14, 2), nullable=True)
    bandwidth_low = Column(Numeric(14, 2), nullable=True)
    bandwidth_high = Column(Numeric(14, 2), nullable=True)
    confidence_score = Column(Numeric(5, 2), nullable=True)
    methodology = Column(String(100), nullable=True)
    similar_projects = Column(JSONB, nullable=True)
    reasoning = Column(Text, nullable=True)
    is_current = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    project = relationship("Project", back_populates="estimations")
