from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas import ValidationReport, PublishRunOut
from app.core.security import require_role
from app.services.validation import generate_validation_report
from app.services.catalogue import publish_catalogue

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/validation-report", response_model=ValidationReport)
def validation_report(
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("editor", "admin")),
):
    return generate_validation_report(db)


@router.post("/catalog/publish", response_model=PublishRunOut)
def catalog_publish(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Publish the catalogue. Only admins can publish."""
    run = publish_catalogue(db, user.username)
    return run


@router.get("/publish-runs", response_model=list[PublishRunOut])
def list_publish_runs(
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("editor", "admin")),
):
    from app.models import PublishRun
    runs = db.query(PublishRun).order_by(PublishRun.published_at.desc()).limit(50).all()
    return runs
