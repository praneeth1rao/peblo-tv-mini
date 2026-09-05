"""Validation report service - checks all entities for publishability issues."""

from sqlalchemy.orm import Session

from app.models import Show, Season, Episode, Artwork
from app.schemas import ValidationIssue, ValidationReport


def generate_validation_report(db: Session) -> ValidationReport:
    """Check all published shows/episodes for blocking issues."""
    issues: list[ValidationIssue] = []

    # Check published shows
    published_shows = db.query(Show).filter(Show.status == "published").all()
    for show in published_shows:
        if not show.section:
            issues.append(ValidationIssue(
                entity_type="show",
                entity_id=str(show.id),
                entity_title=show.title,
                issue="Published show is missing a section",
            ))

    # Check published episodes
    published_episodes = (
        db.query(Episode)
        .join(Show, Episode.show_id == Show.id)
        .filter(Episode.status == "published", Show.status == "published")
        .all()
    )

    for ep in published_episodes:
        if not ep.duration or ep.duration <= 0:
            issues.append(ValidationIssue(
                entity_type="episode",
                entity_id=str(ep.id),
                entity_title=ep.title,
                issue="Published episode is missing a duration",
            ))

        artwork = db.query(Artwork).filter(Artwork.episode_id == ep.id).first()
        if not artwork:
            issues.append(ValidationIssue(
                entity_type="episode",
                entity_id=str(ep.id),
                entity_title=ep.title,
                issue="Published episode is missing artwork",
            ))

    return ValidationReport(
        issues=issues,
        blocking_count=len(issues),
        publishable=len(issues) == 0,
    )
