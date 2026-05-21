import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    subscription_tier = Column(String(50), nullable=False, default="free")
    max_projects = Column(Integer, nullable=False, default=10)
    max_users = Column(Integer, nullable=False, default=5)
    settings = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    users = relationship("User", back_populates="org", foreign_keys="User.organization_id")
    projects = relationship("Project", back_populates="organization", foreign_keys="Project.organization_id")
