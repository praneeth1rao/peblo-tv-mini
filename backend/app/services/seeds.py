"""Seed the database from data/seed_shows.json and data/reference.json."""

import json
import os
import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Show, Season, Episode, User
from app.core.security import hash_password


def _find_data_dir() -> Path:
    """Find data directory - works in local dev and Docker."""
    # Docker: /app/data
    docker_path = Path("/app/data")
    if docker_path.exists():
        return docker_path
    # Local dev: three parents up from services/seeds.py -> backend/app/services -> data/
    local_path = Path(__file__).resolve().parents[3] / "data"
    if local_path.exists():
        return local_path
    # Fallback
    return docker_path


DATA_DIR = _find_data_dir()


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def seed_database(db: Session) -> dict:
    """Seed shows, seasons, episodes, and demo users. Returns counts."""
    counts = {"shows": 0, "seasons": 0, "episodes": 0, "users": 0}

    # Seed demo users if they don't exist
    for uname, role, pw in [("admin", "admin", "admin123"), ("editor", "editor", "editor123")]:
        if not db.query(User).filter(User.username == uname).first():
            db.add(User(username=uname, password_hash=hash_password(pw), role=role))
            counts["users"] += 1
    db.commit()

    # Load seed shows
    seed_path = DATA_DIR / "seed_shows.json"
    if not seed_path.exists():
        return counts

    with open(seed_path) as f:
        shows_data = json.load(f)

    if not shows_data:
        return counts

    for show_data in shows_data:
        slug = show_data.get("slug") or slugify(show_data["title"])
        existing = db.query(Show).filter(Show.slug == slug).first()
        if existing:
            continue

        show = Show(
            title=show_data["title"],
            description=show_data.get("description", ""),
            slug=slug,
            section=show_data.get("section"),
            status=show_data.get("status", "published"),
        )
        db.add(show)
        db.flush()
        counts["shows"] += 1

        for season_data in show_data.get("seasons", []):
            season = Season(
                show_id=show.id,
                number=season_data["number"],
                title=season_data.get("title", f"Season {season_data['number']}"),
                status=season_data.get("status", "published"),
            )
            db.add(season)
            db.flush()
            counts["seasons"] += 1

            for ep_data in season_data.get("episodes", []):
                ep = Episode(
                    season_id=season.id,
                    show_id=show.id,
                    number=ep_data["number"],
                    title=ep_data["title"],
                    description=ep_data.get("description", ""),
                    duration=ep_data.get("duration"),
                    content_group=ep_data.get("content_group", f"{slug}-s{season.number}e{ep_data['number']}"),
                    language=ep_data.get("language", "en"),
                    status=ep_data.get("status", "published"),
                )
                db.add(ep)
                db.flush()
                counts["episodes"] += 1

    db.commit()
    return counts
