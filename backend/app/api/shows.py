from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Show, User
from app.schemas import ShowCreate, ShowUpdate, ShowOut, ShowListOut
from app.core.security import get_current_user, require_role

router = APIRouter(prefix="/shows", tags=["shows"])


@router.get("", response_model=list[ShowListOut])
def list_shows(
    section: Optional[str] = Query(None),
    show_status: Optional[str] = Query(None, alias="status"),
    q: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(Show)
    if section:
        query = query.filter(Show.section == section)
    if show_status:
        query = query.filter(Show.status == show_status)
    if q:
        query = query.filter(Show.title.ilike(f"%{q}%"))
    return query.order_by(Show.title).offset(offset).limit(limit).all()


@router.get("/{show_id}", response_model=ShowOut)
def get_show(show_id: UUID, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return show


@router.post("", response_model=ShowOut, status_code=status.HTTP_201_CREATED)
def create_show(
    data: ShowCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("editor", "admin")),
):
    if db.query(Show).filter(Show.slug == data.slug).first():
        raise HTTPException(status_code=400, detail="A show with this slug already exists")
    show = Show(**data.model_dump())
    db.add(show)
    db.commit()
    db.refresh(show)
    return show


@router.put("/{show_id}", response_model=ShowOut)
def update_show(
    show_id: UUID,
    data: ShowUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("editor", "admin")),
):
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(show, key, value)
    db.commit()
    db.refresh(show)
    return show


@router.delete("/{show_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_show(
    show_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("editor", "admin")),
):
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    db.delete(show)
    db.commit()
