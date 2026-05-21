"""Export router — provides Excel and PDF download endpoints for projects."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.export_service import (
    generate_estimation_excel,
    generate_estimation_pdf,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{project_id}/export/excel")
def export_excel(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Download an .xlsx workbook for the given project."""
    try:
        data = generate_estimation_excel(str(project_id), db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Excel export failed for project %s", project_id)
        raise HTTPException(status_code=500, detail="Excel export mislukt")

    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="project_{project_id}.xlsx"',
            "Content-Length": str(len(data)),
        },
    )


@router.get("/{project_id}/export/pdf")
def export_pdf(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Download a .pdf report for the given project."""
    try:
        data = generate_estimation_pdf(str(project_id), db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("PDF export failed for project %s", project_id)
        raise HTTPException(status_code=500, detail="PDF export mislukt")

    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="project_{project_id}.pdf"',
            "Content-Length": str(len(data)),
        },
    )
