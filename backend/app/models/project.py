import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, Numeric, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    project_number = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    client = Column(String(255), nullable=True)
    location = Column(String(500), nullable=True)
    phase = Column(String(50), nullable=False, default="VO")
    discipline = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(50), nullable=False, default="active", index=True)
    scope_description = Column(Text, nullable=True)
    geometry = Column(Geometry(geometry_type="GEOMETRY", srid=28992), nullable=True)
    budget_estimated = Column(Numeric(14, 2), nullable=True)
    budget_actual = Column(Numeric(14, 2), nullable=True)
    hours_estimated = Column(Numeric(10, 2), nullable=True)
    hours_actual = Column(Numeric(10, 2), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), onupdate=datetime.utcnow)

    creator = relationship("User", back_populates="projects", foreign_keys=[created_by])
    organization = relationship("Organization", back_populates="projects", foreign_keys=[organization_id])
    risks = relationship("Risk", back_populates="project", cascade="all, delete-orphan")
    estimations = relationship("Estimation", back_populates="project", cascade="all, delete-orphan")
    permits = relationship("Permit", back_populates="project", cascade="all, delete-orphan")
