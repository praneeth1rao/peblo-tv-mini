from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from PIL import Image
import io

from app.db.session import get_db
from app.models import Artwork, Show, Episode, User
from app.schemas import ArtworkOut
from app.core.security import get_current_user, require_role
from app.storage import get_storage

router = APIRouter(prefix="/artwork", tags=["artwork"])

ARTWORK_SPECS = {
    "poster": {"target_width": 600, "target_height": 900, "aspect_ratio": 2 / 3, "label": "Poster"},
    "banner": {"target_width": 1280, "target_height": 720, "aspect_ratio": 16 / 9, "label": "Banner"},
    "thumbnail": {"target_width": 640, "target_height": 360, "aspect_ratio": 16 / 9, "label": "Thumbnail"},
}

MAX_FILE_SIZE = 200 * 1024  # 200 KB
ASPECT_TOLERANCE = 0.05  # 5% tolerance on aspect ratio


def validate_artwork(image_bytes: bytes, artwork_type: str) -> tuple[int, int]:
    """Validate image dimensions and aspect ratio. Returns (width, height)."""
    if artwork_type not in ARTWORK_SPECS:
        raise HTTPException(status_code=400, detail=f"Invalid artwork type: {artwork_type}")

    spec = ARTWORK_SPECS[artwork_type]

    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size ({len(image_bytes) // 1024} KB) exceeds the 200 KB limit for {spec['label']} artwork.",
        )

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read image. Please upload a valid image file.")

    actual_ratio = width / height if height > 0 else 0
    expected_ratio = spec["aspect_ratio"]
    if abs(actual_ratio - expected_ratio) / expected_ratio > ASPECT_TOLERANCE:
        raise HTTPException(
            status_code=400,
            detail=(
                f"{spec['label']} artwork has incorrect aspect ratio. "
                f"Got {width}x{height} (ratio {actual_ratio:.2f}), "
                f"expected approximately {spec['target_width']}x{spec['target_height']} "
                f"(ratio {expected_ratio:.2f})."
            ),
        )

    return width, height


@router.get("", response_model=list[ArtworkOut])
def list_artwork(
    show_id: Optional[UUID] = Query(None),
    episode_id: Optional[UUID] = Query(None),
    artwork_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(Artwork)
    if show_id:
        query = query.filter(Artwork.show_id == show_id)
    if episode_id:
        query = query.filter(Artwork.episode_id == episode_id)
    if artwork_type:
        query = query.filter(Artwork.artwork_type == artwork_type)
    return query.all()


@router.get("/{artwork_id}", response_model=ArtworkOut)
def get_artwork(artwork_id: UUID, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    art = db.query(Artwork).filter(Artwork.id == artwork_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return art


@router.post("", response_model=ArtworkOut, status_code=status.HTTP_201_CREATED)
async def upload_artwork(
    artwork_type: str = Form(...),
    show_id: Optional[str] = Form(None),
    episode_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("editor", "admin")),
):
    if artwork_type not in ARTWORK_SPECS:
        raise HTTPException(status_code=400, detail=f"Invalid artwork type: {artwork_type}. Must be poster, banner, or thumbnail.")

    if not show_id and not episode_id:
        raise HTTPException(status_code=400, detail="Artwork must be associated with a show or episode")

    # Validate file
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        spec = ARTWORK_SPECS[artwork_type]
        raise HTTPException(
            status_code=400,
            detail=f"File size ({len(contents) // 1024} KB) exceeds the 200 KB limit for {spec['label']} artwork.",
        )

    width, height = validate_artwork(contents, artwork_type)

    # Validate references exist
    if show_id:
        show_uuid = UUID(show_id)
        if not db.query(Show).filter(Show.id == show_uuid).first():
            raise HTTPException(status_code=404, detail="Show not found")
    else:
        show_uuid = None

    if episode_id:
        ep_uuid = UUID(episode_id)
        if not db.query(Episode).filter(Episode.id == ep_uuid).first():
            raise HTTPException(status_code=404, detail="Episode not found")
    else:
        ep_uuid = None

    # Save file
    storage = get_storage()
    filename = file.filename or f"{artwork_type}.bin"
    rel_path = storage.save(contents, filename, file.content_type or "application/octet-stream")
    url = storage.get_url(rel_path)

    artwork = Artwork(
        artwork_type=artwork_type,
        url=url,
        width=width,
        height=height,
        show_id=show_uuid,
        episode_id=ep_uuid,
    )
    db.add(artwork)
    db.commit()
    db.refresh(artwork)
    return artwork


@router.delete("/{artwork_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artwork(
    artwork_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("editor", "admin")),
):
    art = db.query(Artwork).filter(Artwork.id == artwork_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Artwork not found")
    db.delete(art)
    db.commit()
