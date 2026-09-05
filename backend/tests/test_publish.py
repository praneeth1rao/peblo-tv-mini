"""Tests for validation report, publishing, language grouping, and search."""

from tests.conftest import auth_header, TestSession
from app.models import Show, Season, Episode, Artwork
from app.services.validation import generate_validation_report
from app.services.catalogue import generate_catalogue, publish_catalogue
import io
import os
from PIL import Image


def _make_image(width: int, height: int) -> bytes:
    img = Image.new("RGB", (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_validation_report_missing_section(client, admin_token, db):
    """Published show without section should appear in validation report."""
    show = Show(title="No Section Show", slug="no-section", status="published", section=None)
    db.add(show)
    db.commit()
    report = generate_validation_report(db)
    assert report.blocking_count > 0
    assert any("section" in i.issue.lower() for i in report.issues)


def test_validation_report_missing_duration(client, admin_token, db):
    """Published episode without duration should be flagged."""
    show = Show(title="Dur Show", slug="dur-show", section="Ent", status="published")
    db.add(show)
    db.flush()
    season = Season(show_id=show.id, number=1, title="S1")
    db.add(season)
    db.flush()
    ep = Episode(
        season_id=season.id, show_id=show.id, number=1, title="Ep1",
        content_group="dur-cg", language="en", status="published", duration=None,
    )
    db.add(ep)
    db.commit()
    report = generate_validation_report(db)
    assert report.blocking_count > 0
    assert any("duration" in i.issue.lower() for i in report.issues)


def test_validation_report_missing_artwork(client, admin_token, db):
    """Published episode without artwork should be flagged."""
    show = Show(title="Art Check", slug="art-check", section="Ent", status="published")
    db.add(show)
    db.flush()
    season = Season(show_id=show.id, number=1, title="S1")
    db.add(season)
    db.flush()
    ep = Episode(
        season_id=season.id, show_id=show.id, number=1, title="Ep1",
        content_group="art-cg", language="en", status="published", duration=300,
    )
    db.add(ep)
    db.commit()
    report = generate_validation_report(db)
    assert report.blocking_count > 0
    assert any("artwork" in i.issue.lower() for i in report.issues)


def test_validation_report_publishable(db):
    """A complete published entity should have no blocking issues."""
    show = Show(title="Good Show", slug="good-show", section="Nature", status="published")
    db.add(show)
    db.flush()
    season = Season(show_id=show.id, number=1, title="S1")
    db.add(season)
    db.flush()
    ep = Episode(
        season_id=season.id, show_id=show.id, number=1, title="Ep1",
        content_group="good-cg", language="en", status="published", duration=300,
    )
    db.add(ep)
    db.flush()
    art = Artwork(
        artwork_type="poster", url="/storage/test.png",
        width=600, height=900, episode_id=ep.id,
    )
    db.add(art)
    db.commit()
    report = generate_validation_report(db)
    assert report.publishable is True
    assert report.blocking_count == 0


def test_language_grouping(db):
    """Language variants should collapse in catalogue generation."""
    show = Show(title="Lang Show", slug="lang-show", section="Ent", status="published")
    db.add(show)
    db.flush()
    season = Season(show_id=show.id, number=1, title="S1")
    db.add(season)
    db.flush()
    ep_en = Episode(
        season_id=season.id, show_id=show.id, number=1, title="Episode",
        content_group="lang-cg", language="en", status="published", duration=300,
    )
    ep_es = Episode(
        season_id=season.id, show_id=show.id, number=1, title="Episodio",
        content_group="lang-cg", language="es", status="published", duration=310,
    )
    db.add_all([ep_en, ep_es])
    db.commit()

    cat = generate_catalogue(db, "tester")
    assert cat["total_shows"] == 1
    show_data = cat["shows"][0]
    all_eps = []
    for eps in show_data["seasons"].values():
        all_eps.extend(eps)
    assert len(all_eps) == 1
    assert set(all_eps[0]["languages"]) == {"en", "es"}
    assert all_eps[0]["duration"] == 310  # longest variant


def test_deterministic_ordering(db):
    """Catalogue generation should produce consistent ordering."""
    show = Show(title="Order Show", slug="order-show", section="Ent", status="published")
    db.add(show)
    db.flush()
    season = Season(show_id=show.id, number=1, title="S1")
    db.add(season)
    db.flush()
    for i in range(3, 0, -1):
        ep = Episode(
            season_id=season.id, show_id=show.id, number=i, title=f"Ep {i}",
            content_group=f"order-cg-{i}", language="en", status="published", duration=300,
        )
        db.add(ep)
    db.commit()

    cat1 = generate_catalogue(db, "tester")
    cat2 = generate_catalogue(db, "tester")
    titles1 = []
    for eps in cat1["shows"][0]["seasons"].values():
        titles1.extend([e["number"] for e in eps])
    titles2 = []
    for eps in cat2["shows"][0]["seasons"].values():
        titles2.extend([e["number"] for e in eps])
    assert titles1 == titles2


def test_atomic_publishing_survives_no_crash(db):
    """Normal publish should succeed and create a valid catalogue file."""
    show = Show(title="Pub Show", slug="pub-show", section="Ent", status="published")
    db.add(show)
    db.flush()
    season = Season(show_id=show.id, number=1, title="S1")
    db.add(season)
    db.flush()
    ep = Episode(
        season_id=season.id, show_id=show.id, number=1, title="Ep1",
        content_group="pub-cg", language="en", status="published", duration=300,
    )
    db.add(ep)
    db.commit()

    run = publish_catalogue(db, "admin")
    assert run.status == "success"
    assert run.show_count == 1
    assert run.episode_count == 1
    assert run.catalogue_path is not None
    assert os.path.exists(run.catalogue_path)


def test_search_filters(client, admin_token, db):
    """Search endpoint should filter by section and q."""
    import json

    # Build a catalogue file
    show = Show(title="Search Show", slug="search-show", section="Nature", status="published")
    db.add(show)
    db.flush()
    season = Season(show_id=show.id, number=1, title="S1")
    db.add(season)
    db.flush()
    ep = Episode(
        season_id=season.id, show_id=show.id, number=1, title="Amazing Episode",
        content_group="search-cg", language="en", status="published", duration=300,
    )
    db.add(ep)
    db.commit()

    run = publish_catalogue(db, "admin")

    # Test section filter
    resp = client.get("/catalog/search?section=Nature")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    # Test text search
    resp = client.get("/catalog/search?q=Amazing")
    assert resp.json()["total"] == 1

    # Test language filter
    resp = client.get("/catalog/search?language=en")
    assert resp.json()["total"] == 1

    # Test non-matching filter
    resp = client.get("/catalog/search?section=Nonexistent")
    assert resp.json()["total"] == 0


def test_role_enforcement_editor_cannot_publish(client, editor_token, db):
    """Editors must not be able to publish."""
    resp = client.post("/admin/catalog/publish", headers=auth_header(editor_token))
    assert resp.status_code == 403


def test_role_enforcement_editor_can_read(client, editor_token):
    """Editors should be able to read."""
    resp = client.get("/shows", headers=auth_header(editor_token))
    assert resp.status_code == 200
