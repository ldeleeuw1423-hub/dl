from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel
from decimal import Decimal

from app.database import get_db
from app.models.historical import HistoricalProject
from app.models.project import Project
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


class SimilarProjectResult(BaseModel):
    project: HistoricalProjectOut
    similarity_score: float

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


@router.get("/similar", response_model=List[Dict[str, Any]])
async def find_similar(
    project_id: Optional[UUID] = Query(None, description="Zoek vergelijkbare projecten op basis van een bestaand project"),
    discipline: Optional[str] = None,
    location_type: Optional[str] = None,
    trace_length_m: Optional[float] = None,
    num_crossings: Optional[int] = None,
    num_permits: Optional[int] = None,
    num_stakeholders: Optional[int] = None,
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Find similar historical projects.

    When ``project_id`` is provided the endpoint uses pgvector cosine similarity
    via EstimationService.find_similar_projects. Otherwise it falls back to
    rule-based filtering on discipline, location_type and trace_length_m.
    """
    from app.services.estimation_service import EstimationService

    if project_id is not None:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project is None:
            raise HTTPException(status_code=404, detail="Project niet gevonden")
        project_data = {
            "discipline": discipline or project.discipline,
            "location_type": location_type or "urban",
            "trace_length_m": trace_length_m or 0,
            "num_crossings": num_crossings or 0,
            "num_permits": num_permits or 0,
            "num_stakeholders": num_stakeholders or 0,
        }
        svc = EstimationService(db)
        results = await svc.find_similar_projects(project_data, top_k=top_k)
        output = []
        for hp, score in results:
            output.append({
                "id": str(hp.id),
                "reference_number": hp.reference_number,
                "name": hp.name,
                "discipline": hp.discipline,
                "location_type": hp.location_type,
                "trace_length_m": float(hp.trace_length_m) if hp.trace_length_m else None,
                "num_crossings": hp.num_crossings,
                "num_permits": hp.num_permits,
                "num_stakeholders": hp.num_stakeholders,
                "hours_engineering": float(hp.hours_engineering) if hp.hours_engineering else None,
                "hours_pm": float(hp.hours_pm) if hp.hours_pm else None,
                "hours_om": float(hp.hours_om) if hp.hours_om else None,
                "hours_workprep": float(hp.hours_workprep) if hp.hours_workprep else None,
                "cost_execution": float(hp.cost_execution) if hp.cost_execution else None,
                "cost_total": float(hp.cost_total) if hp.cost_total else None,
                "duration_days": hp.duration_days,
                "num_revisions": hp.num_revisions,
                "risks_count": hp.risks_count,
                "issues_count": hp.issues_count,
                "created_at": hp.created_at.isoformat() if hp.created_at else None,
                "similarity_score": round(score, 4),
            })
        return output

    # Rule-based fallback when no project_id given
    query = db.query(HistoricalProject)
    if discipline:
        query = query.filter(HistoricalProject.discipline == discipline)
    if location_type:
        query = query.filter(HistoricalProject.location_type == location_type)
    if trace_length_m:
        query = query.filter(
            HistoricalProject.trace_length_m.between(trace_length_m * 0.5, trace_length_m * 1.5)
        )
    projects = query.limit(top_k).all()
    return [
        {
            "id": str(hp.id),
            "reference_number": hp.reference_number,
            "name": hp.name,
            "discipline": hp.discipline,
            "location_type": hp.location_type,
            "trace_length_m": float(hp.trace_length_m) if hp.trace_length_m else None,
            "num_crossings": hp.num_crossings,
            "num_permits": hp.num_permits,
            "num_stakeholders": hp.num_stakeholders,
            "hours_engineering": float(hp.hours_engineering) if hp.hours_engineering else None,
            "hours_pm": float(hp.hours_pm) if hp.hours_pm else None,
            "hours_om": float(hp.hours_om) if hp.hours_om else None,
            "hours_workprep": float(hp.hours_workprep) if hp.hours_workprep else None,
            "cost_execution": float(hp.cost_execution) if hp.cost_execution else None,
            "cost_total": float(hp.cost_total) if hp.cost_total else None,
            "duration_days": hp.duration_days,
            "num_revisions": hp.num_revisions,
            "risks_count": hp.risks_count,
            "issues_count": hp.issues_count,
            "created_at": hp.created_at.isoformat() if hp.created_at else None,
            "similarity_score": 0.75,
        }
        for hp in projects
    ]
