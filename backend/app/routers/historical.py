from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel
from decimal import Decimal

from app.database import get_db
from app.models.historical import HistoricalProject
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()


class HistoricalProjectIn(BaseModel):
    reference_number: str
    name: str
    discipline: str
    location_type: str
    trace_length_m: Optional[Decimal] = None
    num_crossings: Optional[int] = None
    num_permits: Optional[int] = None
    num_stakeholders: Optional[int] = None
    hours_engineering: Optional[Decimal] = None
    hours_pm: Optional[Decimal] = None
    hours_om: Optional[Decimal] = None
    hours_workprep: Optional[Decimal] = None
    cost_execution: Optional[Decimal] = None
    cost_total: Optional[Decimal] = None
    duration_days: Optional[int] = None
    num_revisions: Optional[int] = None
    risks_count: Optional[int] = None
    issues_count: Optional[int] = None


class HistoricalProjectOut(HistoricalProjectIn):
    id: UUID
    created_at: Any

    model_config = {"from_attributes": True}


@router.get("", response_model=List[HistoricalProjectOut])
def list_historical(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    discipline: Optional[str] = None,
    location_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(HistoricalProject)
    if discipline:
        query = query.filter(HistoricalProject.discipline == discipline)
    if location_type:
        query = query.filter(HistoricalProject.location_type == location_type)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=HistoricalProjectOut, status_code=status.HTTP_201_CREATED)
def create_historical(
    data: HistoricalProjectIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin", "pm"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or PM required")
    existing = db.query(HistoricalProject).filter(
        HistoricalProject.reference_number == data.reference_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Reference number already exists")
    hp = HistoricalProject(**data.model_dump())
    db.add(hp)
    db.commit()
    db.refresh(hp)
    return hp


@router.get("/similar", response_model=List[HistoricalProjectOut])
def find_similar(
    discipline: Optional[str] = None,
    location_type: Optional[str] = None,
    trace_length_m: Optional[float] = None,
    num_crossings: Optional[int] = None,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(HistoricalProject)
    if discipline:
        query = query.filter(HistoricalProject.discipline == discipline)
    if location_type:
        query = query.filter(HistoricalProject.location_type == location_type)
    if trace_length_m:
        # Find projects within 50% range
        query = query.filter(
            HistoricalProject.trace_length_m.between(trace_length_m * 0.5, trace_length_m * 1.5)
        )
    return query.limit(limit).all()
