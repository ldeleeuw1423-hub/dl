from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import os
import aiofiles

from app.database import get_db
from app.models.project import Project
from app.core.deps import get_current_user
from app.models.user import User
from app.config import settings
from app.services.file_service import FileService

router = APIRouter()


@router.post("/{project_id}/files/upload")
async def upload_file(
    project_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    service = FileService(settings.UPLOAD_DIR)
    saved_path = await service.save_file(str(project_id), file.filename or "upload", content)

    return {
        "filename": file.filename,
        "saved_path": saved_path,
        "size_bytes": len(content),
        "content_type": file.content_type,
    }


@router.get("/{project_id}/files")
def list_files(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    service = FileService(settings.UPLOAD_DIR)
    files = service.list_files(str(project_id))
    return {"files": files}


@router.delete("/{project_id}/files/{filename}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    project_id: UUID,
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    service = FileService(settings.UPLOAD_DIR)
    deleted = service.delete_file(str(project_id), filename)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
