from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class EstimationGenerateRequest(BaseModel):
    discipline: Optional[str] = None
    scope_description: Optional[str] = None
    trace_length_m: Optional[float] = None
    num_crossings: Optional[int] = None
    num_permits: Optional[int] = None
    num_stakeholders: Optional[int] = None
    location_type: Optional[str] = None
    phase: Optional[str] = None


class SimilarProjectRef(BaseModel):
    reference_number: str
    name: str
    similarity_score: float
    hours_total: Optional[float] = None
    cost_total: Optional[float] = None


class EstimationOut(BaseModel):
    id: UUID
    project_id: UUID
    version: int
    discipline: Optional[str] = None
    hours_engineering: Optional[Decimal] = None
    hours_pm: Optional[Decimal] = None
    hours_om: Optional[Decimal] = None
    hours_workprep: Optional[Decimal] = None
    hours_execution: Optional[Decimal] = None
    cost_materials: Optional[Decimal] = None
    cost_total: Optional[Decimal] = None
    bandwidth_low: Optional[Decimal] = None
    bandwidth_high: Optional[Decimal] = None
    confidence_score: Optional[Decimal] = None
    methodology: Optional[str] = None
    similar_projects: Optional[List[Any]] = None
    reasoning: Optional[str] = None
    is_current: bool
    created_at: datetime

    model_config = {"from_attributes": True}
