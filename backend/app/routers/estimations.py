from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.project import Project
from app.models.estimation import Estimation
from app.schemas.estimation import EstimationOut, EstimationGenerateRequest
from app.core.deps import get_current_user
from app.models.user import User
from app.services.estimation_service import EstimationService

router = APIRouter()


@router.get("/{project_id}/estimation", response_model=List[EstimationOut])
def get_estimations(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    estimations = (
        db.query(Estimation)
        .filter(Estimation.project_id == project_id)
        .order_by(Estimation.version.desc())
        .all()
    )
    return estimations


@router.post("/{project_id}/estimation/generate", response_model=EstimationOut)
async def generate_estimation(
    project_id: UUID,
    request: EstimationGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Mark previous estimations as not current
    db.query(Estimation).filter(
        Estimation.project_id == project_id,
        Estimation.is_current == True,
    ).update({"is_current": False})
    db.commit()

    service = EstimationService(db)
    estimation = await service.generate_estimation(project, request)
    return estimation
