import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, Integer, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Permit(Base):
    __tablename__ = "permits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    permit_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    authority = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="required")
    submission_date = Column(Date, nullable=True)
    expected_approval = Column(Date, nullable=True)
    actual_approval = Column(Date, nullable=True)
    risk_level = Column(String(20), nullable=False, default="medium")
    delay_probability = Column(Integer, nullable=True)
    owner = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    auto_detected = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="permits")
