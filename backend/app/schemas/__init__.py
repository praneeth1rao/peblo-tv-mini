from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- Auth ---

class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserOut(BaseModel):
    id: UUID
    username: str
    role: str


# --- Show ---

class ShowCreate(BaseModel):
    title: str = Field(..., max_length=500)
    description: str = ""
    slug: str = Field(..., max_length=500)
    section: Optional[str] = None
    status: str = "draft"


class ShowUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None
    section: Optional[str] = None
    status: Optional[str] = None


class ShowOut(BaseModel):
    id: UUID
    title: str
    description: str
    slug: str
    section: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShowListOut(BaseModel):
    id: UUID
    title: str
    slug: str
    section: Optional[str]
    status: str

    model_config = {"from_attributes": True}


# --- Season ---

class SeasonCreate(BaseModel):
    show_id: UUID
    number: int
    title: str = ""
    status: str = "draft"


class SeasonUpdate(BaseModel):
    number: Optional[int] = None
    title: Optional[str] = None
    status: Optional[str] = None


class SeasonOut(BaseModel):
    id: UUID
    show_id: UUID
    number: int
    title: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Episode ---

class EpisodeCreate(BaseModel):
    season_id: UUID
    show_id: UUID
    number: int
    title: str = Field(..., max_length=500)
    description: str = ""
    duration: Optional[int] = None
    content_group: str = "default"
    language: str = "en"
    status: str = "draft"


class EpisodeUpdate(BaseModel):
    number: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    content_group: Optional[str] = None
    language: Optional[str] = None
    status: Optional[str] = None


class EpisodeOut(BaseModel):
    id: UUID
    season_id: UUID
    show_id: UUID
    number: int
    title: str
    description: str
    duration: Optional[int]
    content_group: str
    language: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Artwork ---

class ArtworkOut(BaseModel):
    id: UUID
    artwork_type: str
    url: str
    width: int
    height: int
    show_id: Optional[UUID]
    episode_id: Optional[UUID]
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Publish ---

class PublishRunOut(BaseModel):
    id: UUID
    status: str
    published_by: str
    published_at: Optional[datetime]
    show_count: int
    season_count: int
    episode_count: int
    error_message: Optional[str]

    model_config = {"from_attributes": True}


# --- Catalogue ---

class CatalogueEpisode(BaseModel):
    id: str
    number: int
    title: str
    description: str
    duration: Optional[int]
    content_group: str
    languages: list[str]
    artwork: dict
    season_number: int


class CatalogueShow(BaseModel):
    id: str
    title: str
    description: str
    slug: str
    section: str
    artwork: dict
    seasons: dict  # season_number -> list of episodes


class Catalogue(BaseModel):
    generated_at: str
    generated_by: str
    shows: list[CatalogueShow]
    total_shows: int
    total_episodes: int


# --- Validation ---

class ValidationIssue(BaseModel):
    entity_type: str
    entity_id: str
    entity_title: str
    issue: str


class ValidationReport(BaseModel):
    issues: list[ValidationIssue]
    blocking_count: int
    publishable: bool
