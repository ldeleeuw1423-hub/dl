from pydantic import BaseModel, field_validator
from typing import Optional, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal


class ProjectBase(BaseModel):
    project_number: str
    name: str
    client: Optional[str] = None
    location: Optional[str] = None
    phase: str = "VO"
    discipline: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "active"
    scope_description: Optional[str] = None
    budget_estimated: Optional[Decimal] = None
    budget_actual: Optional[Decimal] = None
    hours_estimated: Optional[Decimal] = None
    hours_actual: Optional[Decimal] = None

    @field_validator("phase")
    @classmethod
    def valid_phase(cls, v: str) -> str:
        allowed = {"VO", "DO", "UO", "Realisatie"}
        if v not in allowed:
            raise ValueError(f"Phase must be one of {allowed}")
        return v

    @field_validator("discipline")
    @classmethod
    def valid_discipline(cls, v: str) -> str:
        allowed = {"Gas", "Elektra", "LS_MS", "Stations"}
        if v not in allowed:
            raise ValueError(f"Discipline must be one of {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"active", "on_hold", "completed", "cancelled"}
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v


class ProjectCreate(ProjectBase):
    geometry: Optional[Any] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client: Optional[str] = None
    location: Optional[str] = None
    phase: Optional[str] = None
    discipline: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    scope_description: Optional[str] = None
    budget_estimated: Optional[Decimal] = None
    budget_actual: Optional[Decimal] = None
    hours_estimated: Optional[Decimal] = None
    hours_actual: Optional[Decimal] = None
    geometry: Optional[Any] = None


class ProjectOut(ProjectBase):
    id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListOut(BaseModel):
    id: UUID
    project_number: str
    name: str
    client: Optional[str] = None
    location: Optional[str] = None
    phase: str
    discipline: str
    status: str
    budget_estimated: Optional[Decimal] = None
    hours_estimated: Optional[Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: datetime
    risks_count: int = 0
    permits_count: int = 0

    model_config = {"from_attributes": True}
