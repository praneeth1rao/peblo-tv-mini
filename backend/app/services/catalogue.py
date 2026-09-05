"""Catalogue publishing service.

Generates a complete catalogue JSON from published data and atomically
replaces the live file. If publishing crashes halfway, the previous
catalogue remains available.
"""

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Show, Season, Episode, Artwork, PublishRun
from app.core.config import settings


def _get_artwork_map(db: Session, episode_id) -> dict:
    """Get artwork dict for an episode."""
    arts = db.query(Artwork).filter(Artwork.episode_id == episode_id).all()
    return {a.artwork_type: {"url": a.url, "width": a.width, "height": a.height} for a in arts}


def _get_show_artwork(db: Session, show_id) -> dict:
    """Get artwork dict for a show."""
    arts = db.query(Artwork).filter(Artwork.show_id == show_id).all()
    return {a.artwork_type: {"url": a.url, "width": a.width, "height": a.height} for a in arts}


def generate_catalogue(db: Session, published_by: str) -> dict:
    """Generate the complete catalogue from published data.

    - Only includes published shows and published episodes.
    - Collapses language variants using content_group.
    - Groups by section.
    - Uses deterministic ordering.
    """
    published_shows = (
        db.query(Show)
        .filter(Show.status == "published")
        .order_by(Show.title)
        .all()
    )

    shows_catalogue = []
    total_episodes = 0

    for show in published_shows:
        show_artwork = _get_show_artwork(db, show.id)

        # Get published episodes for this show
        episodes = (
            db.query(Episode)
            .filter(Episode.show_id == show.id, Episode.status == "published")
            .order_by(Episode.season_id, Episode.number)
            .all()
        )

        # Group by content_group and collapse language variants
        grouped: dict[str, dict] = {}
        for ep in episodes:
            cg = ep.content_group
            if cg not in grouped:
                grouped[cg] = {
                    "id": cg,
                    "number": ep.number,
                    "title": ep.title,
                    "description": ep.description,
                    "duration": ep.duration,
                    "content_group": cg,
                    "languages": set(),
                    "artwork": _get_artwork_map(db, ep.id),
                    "season_number": ep.season.number if ep.season else 0,
                }
            grouped[cg]["languages"].add(ep.language)
            # Use the longest duration if variants differ
            if ep.duration and (not grouped[cg]["duration"] or ep.duration > grouped[cg]["duration"]):
                grouped[cg]["duration"] = ep.duration
            # Merge artwork from any variant that has it
            ep_art = _get_artwork_map(db, ep.id)
            for atype, adata in ep_art.items():
                if atype not in grouped[cg]["artwork"]:
                    grouped[cg]["artwork"][atype] = adata

        # Sort by season then episode number
        episodes_list = sorted(
            grouped.values(), key=lambda e: (e["season_number"], e["number"])
        )

        # Convert languages set to sorted list
        for ep in episodes_list:
            ep["languages"] = sorted(ep["languages"])

        # Group episodes by season
        seasons_dict: dict[int, list] = {}
        for ep in episodes_list:
            sn = ep["season_number"]
            # Skip season 0 (trailers) in normal display
            if sn not in seasons_dict:
                seasons_dict[sn] = []
            seasons_dict[sn].append(ep)

        total_episodes += len(episodes_list)

        shows_catalogue.append({
            "id": str(show.id),
            "title": show.title,
            "description": show.description,
            "slug": show.slug,
            "section": show.section or "Uncategorized",
            "artwork": show_artwork,
            "seasons": seasons_dict,
        })

    # Group shows by section
    sections: dict[str, list] = {}
    for s in shows_catalogue:
        sec = s["section"]
        if sec not in sections:
            sections[sec] = []
        sections[sec].append(s)

    catalogue = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": published_by,
        "shows": shows_catalogue,
        "sections": sections,
        "total_shows": len(shows_catalogue),
        "total_episodes": total_episodes,
    }

    return catalogue


def publish_catalogue(db: Session, published_by: str) -> PublishRun:
    """Atomically generate and publish the catalogue.

    1. Create a pending PublishRun
    2. Generate the full catalogue to a temp file
    3. Atomically move the temp file to the final location
    4. Update the PublishRun to success
    5. If anything fails, the old catalogue stays intact
    """
    catalogue_dir = settings.CATALOGUE_DIR
    os.makedirs(catalogue_dir, exist_ok=True)

    final_path = os.path.join(catalogue_dir, "catalogue.json")

    run = PublishRun(
        status="pending",
        published_by=published_by,
        published_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        catalogue = generate_catalogue(db, published_by)

        # Write to a temp file in the same directory for atomic rename
        tmp_fd, tmp_path = tempfile.mkstemp(dir=catalogue_dir, suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w") as f:
                json.dump(catalogue, f, indent=2)

            # Atomic rename (same filesystem)
            os.replace(tmp_path, final_path)
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        run.status = "success"
        run.show_count = catalogue["total_shows"]
        run.episode_count = catalogue["total_episodes"]
        run.catalogue_path = final_path
        db.commit()
        db.refresh(run)

    except Exception as e:
        run.status = "failed"
        run.error_message = str(e)
        db.commit()
        db.refresh(run)
        raise

    return run
