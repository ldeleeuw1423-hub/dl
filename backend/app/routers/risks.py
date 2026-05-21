from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.project import Project
from app.models.risk import Risk
from app.schemas.risk import RiskCreate, RiskUpdate, RiskOut
from app.core.deps import get_current_user
from app.models.user import User
from app.services.risk_service import RiskService

router = APIRouter()


def get_project_or_404(project_id: UUID, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("/{project_id}/risks", response_model=List[RiskOut])
def list_risks(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project_or_404(project_id, db)
    risks = db.query(Risk).filter(Risk.project_id == project_id).order_by(Risk.score.desc()).all()
    return risks


@router.post("/{project_id}/risks", response_model=RiskOut, status_code=status.HTTP_201_CREATED)
def create_risk(
    project_id: UUID,
    risk_in: RiskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project_or_404(project_id, db)
    risk = Risk(
        **risk_in.model_dump(),
        project_id=project_id,
        score=risk_in.probability * risk_in.impact,
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk


@router.put("/{project_id}/risks/{risk_id}", response_model=RiskOut)
def update_risk(
    project_id: UUID,
    risk_id: UUID,
    risk_in: RiskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    risk = db.query(Risk).filter(Risk.id == risk_id, Risk.project_id == project_id).first()
    if not risk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found")
    update_data = risk_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(risk, field, value)
    # recalculate score
    risk.score = risk.probability * risk.impact
    db.commit()
    db.refresh(risk)
    return risk


@router.delete("/{project_id}/risks/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_risk(
    project_id: UUID,
    risk_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    risk = db.query(Risk).filter(Risk.id == risk_id, Risk.project_id == project_id).first()
    if not risk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found")
    db.delete(risk)
    db.commit()


@router.post("/{project_id}/risks/auto-detect", response_model=List[RiskOut])
def auto_detect_risks(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_or_404(project_id, db)
    service = RiskService(db)
    risks = service.auto_detect_risks(project)
    return risks
