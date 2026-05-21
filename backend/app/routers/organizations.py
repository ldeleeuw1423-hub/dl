"""Organizations router — multi-tenant organization management."""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization
from app.models.project import Project
from app.models.risk import Risk
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class OrganizationSettings(BaseModel):
    hourly_rate_engineering: Optional[float] = None
    hourly_rate_pm: Optional[float] = None
    hourly_rate_om: Optional[float] = None
    hourly_rate_workprep: Optional[float] = None
    hourly_rate_execution: Optional[float] = None
    risk_threshold_high: Optional[int] = None
    risk_threshold_critical: Optional[int] = None
    custom_disciplines: Optional[List[str]] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class OrganizationOut(BaseModel):
    id: UUID
    name: str
    slug: str
    subscription_tier: str
    max_projects: int
    max_users: int
    settings: Optional[Dict[str, Any]]
    created_at: Any

    model_config = {"from_attributes": True}


class UserInOrg(BaseModel):
    id: UUID
    email: str
    name: str
    role: str
    is_active: bool
    created_at: Any

    model_config = {"from_attributes": True}


class InviteRequest(BaseModel):
    email: EmailStr
    name: str
    role: str = "engineer"


class OrgStats(BaseModel):
    total_projects: int
    active_projects: int
    total_risks: int
    open_risks: int
    high_risk_projects: int
    users_count: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_org_or_404(current_user: User, db: Session) -> Organization:
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gebruiker heeft geen organisatie",
        )
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisatie niet gevonden",
        )
    return org


def _require_admin(current_user: User) -> None:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Alleen beheerders mogen deze actie uitvoeren",
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/me", response_model=OrganizationOut)
def get_my_organization(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Organization:
    """Return the current user's organization."""
    return _get_org_or_404(current_user, db)


@router.put("/me", response_model=OrganizationOut)
def update_my_organization(
    body: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Organization:
    """Update organization name or settings (admin only)."""
    _require_admin(current_user)
    org = _get_org_or_404(current_user, db)

    if body.name is not None:
        org.name = body.name
    if body.settings is not None:
        existing = dict(org.settings or {})
        existing.update(body.settings)
        org.settings = existing

    db.commit()
    db.refresh(org)
    return org


@router.get("/me/users", response_model=List[UserInOrg])
def list_org_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[User]:
    """List all users in the current organization."""
    org = _get_org_or_404(current_user, db)
    return db.query(User).filter(User.organization_id == org.id).all()


@router.post("/invite", response_model=UserInOrg, status_code=status.HTTP_201_CREATED)
def invite_user(
    body: InviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Invite a user to the organization by creating an account (admin only).

    In a production system this would send an e-mail with a set-password link.
    For now it creates an account with a placeholder hashed password.
    """
    _require_admin(current_user)
    org = _get_org_or_404(current_user, db)

    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="E-mailadres is al in gebruik")

    # Count current users
    current_count = db.query(User).filter(User.organization_id == org.id).count()
    if current_count >= org.max_users:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum aantal gebruikers ({org.max_users}) bereikt voor dit abonnement",
        )

    valid_roles = {"admin", "pm", "engineer", "om", "viewer"}
    if body.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Ongeldig rol. Kies uit: {', '.join(sorted(valid_roles))}")

    # Placeholder password — user must reset via set-password flow
    from passlib.context import CryptContext
    import secrets
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    tmp_password = secrets.token_urlsafe(24)

    new_user = User(
        email=body.email,
        name=body.name,
        role=body.role,
        organization_id=org.id,
        hashed_password=pwd_ctx.hash(tmp_password),
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(
        "Gebruiker %s uitgenodigd voor organisatie %s door %s",
        body.email,
        org.name,
        current_user.email,
    )
    return new_user


@router.get("/me/stats", response_model=OrgStats)
def get_org_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrgStats:
    """Return organization-wide KPIs."""
    org = _get_org_or_404(current_user, db)

    total_projects = db.query(Project).filter(Project.organization_id == org.id).count()
    active_projects = (
        db.query(Project)
        .filter(Project.organization_id == org.id, Project.status == "active")
        .count()
    )

    project_ids = [
        row[0]
        for row in db.query(Project.id).filter(Project.organization_id == org.id).all()
    ]

    total_risks = 0
    open_risks = 0
    high_risk_projects = set()

    if project_ids:
        total_risks = db.query(Risk).filter(Risk.project_id.in_(project_ids)).count()
        open_risks = (
            db.query(Risk)
            .filter(Risk.project_id.in_(project_ids), Risk.status == "open")
            .count()
        )
        # Projects with at least one high-score risk
        high_risks = (
            db.query(Risk.project_id)
            .filter(Risk.project_id.in_(project_ids), Risk.score >= 15)
            .distinct()
            .all()
        )
        high_risk_projects = {str(r[0]) for r in high_risks}

    users_count = db.query(User).filter(User.organization_id == org.id).count()

    return OrgStats(
        total_projects=total_projects,
        active_projects=active_projects,
        total_risks=total_risks,
        open_risks=open_risks,
        high_risk_projects=len(high_risk_projects),
        users_count=users_count,
    )
