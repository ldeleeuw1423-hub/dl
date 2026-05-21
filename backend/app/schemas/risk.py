from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, date
from uuid import UUID


class RiskBase(BaseModel):
    description: str
    category: str
    probability: int
    impact: int
    owner: Optional[str] = None
    mitigation_measure: Optional[str] = None
    deadline: Optional[date] = None
    status: str = "open"
    residual_risk: Optional[int] = None
    source: str = "manual"

    @field_validator("probability", "impact")
    @classmethod
    def valid_score_range(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("Value must be between 1 and 5")
        return v

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"open", "mitigated", "accepted", "closed"}
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v

    @field_validator("source")
    @classmethod
    def valid_source(cls, v: str) -> str:
        allowed = {"gis", "ai", "manual"}
        if v not in allowed:
            raise ValueError(f"Source must be one of {allowed}")
        return v


class RiskCreate(RiskBase):
    pass


class RiskUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    probability: Optional[int] = None
    impact: Optional[int] = None
    owner: Optional[str] = None
    mitigation_measure: Optional[str] = None
    deadline: Optional[date] = None
    status: Optional[str] = None
    residual_risk: Optional[int] = None


class RiskOut(RiskBase):
    id: UUID
    project_id: UUID
    score: int
    auto_detected: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
