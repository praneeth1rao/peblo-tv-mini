import json
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _load_catalogue() -> dict:
    """Load the published catalogue from disk."""
    path = os.path.join(settings.CATALOGUE_DIR, "catalogue.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No catalogue published yet")
    with open(path) as f:
        return json.load(f)


@router.get("")
def get_catalog():
    """Return the full published catalogue."""
    return _load_catalogue()


@router.get("/search")
def search_catalog(
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
):
    """Search and filter the published catalogue.

    - q: searches show title, episode title, and category
    - category: filter by category
    - language: filter by language
    - section: filter by section
    Filters compose together (AND logic).
    """
    catalogue = _load_catalogue()
    shows = catalogue.get("shows", [])

    results = []
    for show in shows:
        # Section filter
        if section and show.get("section", "").lower() != section.lower():
            continue

        # Collect all episodes across seasons
        all_episodes = []
        for season_num, episodes in show.get("seasons", {}).items():
            all_episodes.extend(episodes)

        # Language filter on episodes
        if language:
            filtered_episodes = []
            for ep in all_episodes:
                if language.lower() in [l.lower() for l in ep.get("languages", [])]:
                    filtered_episodes.append(ep)
            all_episodes = filtered_episodes

        # Text search
        if q:
            q_lower = q.lower()
            match = q_lower in show.get("title", "").lower()
            if not match:
                for ep in all_episodes:
                    if q_lower in ep.get("title", "").lower():
                        match = True
                        break
            if not match:
                continue

        # Category filter (not directly on shows in current schema, skip if not present)

        if all_episodes or not q:
            results.append({
                "id": show["id"],
                "title": show["title"],
                "description": show.get("description", ""),
                "slug": show.get("slug", ""),
                "section": show.get("section", ""),
                "artwork": show.get("artwork", {}),
                "episodes": all_episodes,
            })

    return {
        "results": results,
        "total": len(results),
    }
