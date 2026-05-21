from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models.project import Project
from app.models.risk import Risk
from app.models.permit import Permit
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut, ProjectListOut
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("", response_model=List[ProjectListOut])
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    discipline: Optional[str] = None,
    phase: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Project)
    if status:
        query = query.filter(Project.status == status)
    if discipline:
        query = query.filter(Project.discipline == discipline)
    if phase:
        query = query.filter(Project.phase == phase)
    if search:
        query = query.filter(
            Project.name.ilike(f"%{search}%") |
            Project.project_number.ilike(f"%{search}%") |
            Project.client.ilike(f"%{search}%")
        )
    projects = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for p in projects:
        risks_count = db.query(func.count(Risk.id)).filter(Risk.project_id == p.id).scalar()
        permits_count = db.query(func.count(Permit.id)).filter(Permit.project_id == p.id).scalar()
        item = ProjectListOut.model_validate(p)
        item.risks_count = risks_count or 0
        item.permits_count = permits_count or 0
        result.append(item)
    return result


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Project).filter(Project.project_number == project_in.project_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project number {project_in.project_number} already exists",
        )
    project_data = project_in.model_dump(exclude={"geometry"})
    project = Project(**project_data, created_by=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: UUID,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    update_data = project_in.model_dump(exclude_unset=True, exclude={"geometry"})
    for field, value in update_data.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if current_user.role not in ("admin", "pm"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    db.delete(project)
    db.commit()
