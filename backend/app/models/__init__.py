import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, ForeignKey,
    UniqueConstraint, Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_id():
    return uuid.uuid4()


class Show(Base):
    __tablename__ = "shows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_id)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True, default="")
    slug = Column(String(500), nullable=False, unique=True)
    section = Column(String(200), nullable=True)
    status = Column(String(20), nullable=False, default="draft")  # draft | published
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    seasons = relationship("Season", back_populates="show", cascade="all, delete-orphan", order_by="Season.number")
    episodes = relationship("Episode", back_populates="show", cascade="all, delete-orphan")
    artwork = relationship("Artwork", back_populates="show", cascade="all, delete-orphan")


class Season(Base):
    __tablename__ = "seasons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_id)
    show_id = Column(UUID(as_uuid=True), ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)
    number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=True, default="")
    status = Column(String(20), nullable=False, default="draft")  # draft | published
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    show = relationship("Show", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan", order_by="Episode.number")

    __table_args__ = (
        UniqueConstraint("show_id", "number", name="uq_season_show_number"),
    )


class Episode(Base):
    __tablename__ = "episodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_id)
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    show_id = Column(UUID(as_uuid=True), ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)
    number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True, default="")
    duration = Column(Integer, nullable=True)  # seconds
    content_group = Column(String(200), nullable=False, default="default")
    language = Column(String(10), nullable=False, default="en")
    status = Column(String(20), nullable=False, default="draft")  # draft | published
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    show = relationship("Show", back_populates="episodes")
    season = relationship("Season", back_populates="episodes")
    artwork = relationship("Artwork", back_populates="episode", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("content_group", "language", name="uq_episode_content_group_language"),
    )


class Artwork(Base):
    __tablename__ = "artwork"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_id)
    artwork_type = Column(String(20), nullable=False)  # poster | banner | thumbnail
    url = Column(String(1000), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    show_id = Column(UUID(as_uuid=True), ForeignKey("shows.id", ondelete="CASCADE"), nullable=True)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    show = relationship("Show", back_populates="artwork")
    episode = relationship("Episode", back_populates="artwork")


class PublishRun(Base):
    __tablename__ = "publish_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_id)
    status = Column(String(20), nullable=False, default="pending")  # pending | success | failed
    published_by = Column(String(200), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    show_count = Column(Integer, nullable=False, default=0)
    season_count = Column(Integer, nullable=False, default=0)
    episode_count = Column(Integer, nullable=False, default=0)
    catalogue_path = Column(String(1000), nullable=True)
    error_message = Column(Text, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_id)
    username = Column(String(200), nullable=False, unique=True)
    password_hash = Column(String(500), nullable=False)
    role = Column(String(20), nullable=False, default="editor")  # editor | admin
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
