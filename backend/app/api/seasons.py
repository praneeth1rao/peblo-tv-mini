from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Season, Show, User
from app.schemas import SeasonCreate, SeasonUpdate, SeasonOut
from app.core.security import get_current_user, require_role

router = APIRouter(prefix="/seasons", tags=["seasons"])


@router.get("", response_model=list[SeasonOut])
def list_seasons(
    show_id: Optional[UUID] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(Season)
    if show_id:
        query = query.filter(Season.show_id == show_id)
    return query.order_by(Season.number).offset(offset).limit(limit).all()


@router.get("/{season_id}", response_model=SeasonOut)
def get_season(season_id: UUID, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    season = db.query(Season).filter(Season.id == season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    return season


@router.post("", response_model=SeasonOut, status_code=status.HTTP_201_CREATED)
def create_season(
    data: SeasonCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("editor", "admin")),
):
    show = db.query(Show).filter(Show.id == data.show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    existing = (
        db.query(Season)
        .filter(Season.show_id == data.show_id, Season.number == data.number)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Season number already exists for this show")
    season = Season(**data.model_dump())
    db.add(season)
    db.commit()
    db.refresh(season)
    return season


@router.put("/{season_id}", response_model=SeasonOut)
def update_season(
    season_id: UUID,
    data: SeasonUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("editor", "admin")),
):
    season = db.query(Season).filter(Season.id == season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(season, key, value)
    db.commit()
    db.refresh(season)
    return season


@router.delete("/{season_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_season(
    season_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("editor", "admin")),
):
    season = db.query(Season).filter(Season.id == season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    db.delete(season)
    db.commit()
