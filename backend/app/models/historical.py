import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class HistoricalProject(Base):
    __tablename__ = "historical_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    reference_number = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    discipline = Column(String(50), nullable=False, index=True)
    location_type = Column(String(50), nullable=False)
    trace_length_m = Column(Numeric(10, 2), nullable=True)
    num_crossings = Column(Integer, nullable=True)
    num_permits = Column(Integer, nullable=True)
    num_stakeholders = Column(Integer, nullable=True)
    hours_engineering = Column(Numeric(10, 2), nullable=True)
    hours_pm = Column(Numeric(10, 2), nullable=True)
    hours_om = Column(Numeric(10, 2), nullable=True)
    hours_workprep = Column(Numeric(10, 2), nullable=True)
    cost_execution = Column(Numeric(14, 2), nullable=True)
    cost_total = Column(Numeric(14, 2), nullable=True)
    duration_days = Column(Integer, nullable=True)
    num_revisions = Column(Integer, nullable=True)
    risks_count = Column(Integer, nullable=True)
    issues_count = Column(Integer, nullable=True)
    # embedding stored as text for portability; vector operations done via raw SQL
    embedding = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
