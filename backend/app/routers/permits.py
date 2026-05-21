from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.project import Project
from app.models.permit import Permit
from app.schemas.permit import PermitCreate, PermitUpdate, PermitOut
from app.core.deps import get_current_user
from app.models.user import User
from app.services.permit_service import PermitService

router = APIRouter()


def get_project_or_404(project_id: UUID, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("/{project_id}/permits", response_model=List[PermitOut])
def list_permits(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project_or_404(project_id, db)
    permits = db.query(Permit).filter(Permit.project_id == project_id).order_by(Permit.expected_approval).all()
    return permits


@router.post("/{project_id}/permits", response_model=PermitOut, status_code=status.HTTP_201_CREATED)
def create_permit(
    project_id: UUID,
    permit_in: PermitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project_or_404(project_id, db)
    permit = Permit(**permit_in.model_dump(), project_id=project_id)
    db.add(permit)
    db.commit()
    db.refresh(permit)
    return permit


@router.put("/{project_id}/permits/{permit_id}", response_model=PermitOut)
def update_permit(
    project_id: UUID,
    permit_id: UUID,
    permit_in: PermitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    permit = db.query(Permit).filter(Permit.id == permit_id, Permit.project_id == project_id).first()
    if not permit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permit not found")
    update_data = permit_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(permit, field, value)
    db.commit()
    db.refresh(permit)
    return permit


@router.delete("/{project_id}/permits/{permit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permit(
    project_id: UUID,
    permit_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    permit = db.query(Permit).filter(Permit.id == permit_id, Permit.project_id == project_id).first()
    if not permit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permit not found")
    db.delete(permit)
    db.commit()


@router.post("/{project_id}/permits/auto-detect", response_model=List[PermitOut])
def auto_detect_permits(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_or_404(project_id, db)
    service = PermitService(db)
    permits = service.auto_detect_permits(project)
    return permits
