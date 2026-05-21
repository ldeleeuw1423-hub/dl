from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, date
from uuid import UUID


class PermitBase(BaseModel):
    permit_type: str
    description: Optional[str] = None
    authority: str
    status: str = "required"
    submission_date: Optional[date] = None
    expected_approval: Optional[date] = None
    actual_approval: Optional[date] = None
    risk_level: str = "medium"
    delay_probability: Optional[int] = None
    owner: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("authority")
    @classmethod
    def valid_authority(cls, v: str) -> str:
        allowed = {"gemeente", "provincie", "waterschap", "prorail", "rws", "overig"}
        if v not in allowed:
            raise ValueError(f"Authority must be one of {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"required", "in_preparation", "submitted", "approved", "rejected", "not_required"}
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v

    @field_validator("risk_level")
    @classmethod
    def valid_risk_level(cls, v: str) -> str:
        allowed = {"low", "medium", "high", "critical"}
        if v not in allowed:
            raise ValueError(f"Risk level must be one of {allowed}")
        return v

    @field_validator("delay_probability")
    @classmethod
    def valid_delay_prob(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not 0 <= v <= 100:
            raise ValueError("Delay probability must be between 0 and 100")
        return v


class PermitCreate(PermitBase):
    pass


class PermitUpdate(BaseModel):
    permit_type: Optional[str] = None
    description: Optional[str] = None
    authority: Optional[str] = None
    status: Optional[str] = None
    submission_date: Optional[date] = None
    expected_approval: Optional[date] = None
    actual_approval: Optional[date] = None
    risk_level: Optional[str] = None
    delay_probability: Optional[int] = None
    owner: Optional[str] = None
    notes: Optional[str] = None


class PermitOut(PermitBase):
    id: UUID
    project_id: UUID
    auto_detected: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
