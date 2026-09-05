from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Episode, Season, Show, User
from app.schemas import EpisodeCreate, EpisodeUpdate, EpisodeOut
from app.core.security import get_current_user, require_role

router = APIRouter(prefix="/episodes", tags=["episodes"])


@router.get("", response_model=list[EpisodeOut])
def list_episodes(
    show_id: Optional[UUID] = Query(None),
    season_id: Optional[UUID] = Query(None),
    content_group: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    episode_status: Optional[str] = Query(None, alias="status"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(Episode)
    if show_id:
        query = query.filter(Episode.show_id == show_id)
    if season_id:
        query = query.filter(Episode.season_id == season_id)
    if content_group:
        query = query.filter(Episode.content_group == content_group)
    if language:
        query = query.filter(Episode.language == language)
    if episode_status:
        query = query.filter(Episode.status == episode_status)
    return query.order_by(Episode.number).offset(offset).limit(limit).all()


@router.get("/{episode_id}", response_model=EpisodeOut)
def get_episode(episode_id: UUID, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode


@router.post("", response_model=EpisodeOut, status_code=status.HTTP_201_CREATED)
def create_episode(
    data: EpisodeCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("editor", "admin")),
):
    season = db.query(Season).filter(Season.id == data.season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    show = db.query(Show).filter(Show.id == data.show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    existing = (
        db.query(Episode)
        .filter(Episode.content_group == data.content_group, Episode.language == data.language)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Episode with content_group='{data.content_group}' and language='{data.language}' already exists",
        )
    episode = Episode(**data.model_dump())
    db.add(episode)
    db.commit()
    db.refresh(episode)
    return episode


@router.put("/{episode_id}", response_model=EpisodeOut)
def update_episode(
    episode_id: UUID,
    data: EpisodeUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("editor", "admin")),
):
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    updates = data.model_dump(exclude_unset=True)
    # Check uniqueness if content_group or language changing
    cg = updates.get("content_group", episode.content_group)
    lang = updates.get("language", episode.language)
    conflict = (
        db.query(Episode)
        .filter(Episode.content_group == cg, Episode.language == lang, Episode.id != episode_id)
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=400,
            detail=f"Episode with content_group='{cg}' and language='{lang}' already exists",
        )
    for key, value in updates.items():
        setattr(episode, key, value)
    db.commit()
    db.refresh(episode)
    return episode


@router.delete("/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_episode(
    episode_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("editor", "admin")),
):
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    db.delete(episode)
    db.commit()
