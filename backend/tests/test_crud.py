from tests.conftest import auth_header, TestSession
from app.models import Show, Season, Episode


def _create_show(client, token, slug="test-show"):
    resp = client.post("/shows", headers=auth_header(token), json={
        "title": "Test Show",
        "description": "A test show",
        "slug": slug,
        "section": "Entertainment",
    })
    return resp


def _create_season(client, token, show_id, number=1):
    resp = client.post("/seasons", headers=auth_header(token), json={
        "show_id": str(show_id),
        "number": number,
        "title": f"Season {number}",
    })
    return resp


def test_show_create(client, editor_token):
    resp = _create_show(client, editor_token)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Show"
    assert data["slug"] == "test-show"


def test_show_create_duplicate_slug(client, editor_token):
    _create_show(client, editor_token, "dup-slug")
    resp = _create_show(client, editor_token, "dup-slug")
    assert resp.status_code == 400


def test_show_list(client, editor_token):
    _create_show(client, editor_token, "list-1")
    _create_show(client, editor_token, "list-2")
    resp = client.get("/shows", headers=auth_header(editor_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


def test_show_update(client, editor_token):
    create = _create_show(client, editor_token)
    show_id = create.json()["id"]
    resp = client.put(f"/shows/{show_id}", headers=auth_header(editor_token), json={"title": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


def test_show_delete(client, editor_token):
    create = _create_show(client, editor_token, "del-show")
    show_id = create.json()["id"]
    resp = client.delete(f"/shows/{show_id}", headers=auth_header(editor_token))
    assert resp.status_code == 204


def test_season_create(client, editor_token):
    show = _create_show(client, editor_token, "season-show").json()
    resp = _create_season(client, editor_token, show["id"])
    assert resp.status_code == 201
    assert resp.json()["number"] == 1


def test_season_duplicate_number(client, editor_token):
    show = _create_show(client, editor_token, "dup-season").json()
    _create_season(client, editor_token, show["id"], 1)
    resp = _create_season(client, editor_token, show["id"], 1)
    assert resp.status_code == 400


def test_episode_create(client, editor_token):
    show = _create_show(client, editor_token, "ep-show").json()
    season = _create_season(client, editor_token, show["id"]).json()
    resp = client.post("/episodes", headers=auth_header(editor_token), json={
        "show_id": show["id"],
        "season_id": season["id"],
        "number": 1,
        "title": "Pilot",
        "content_group": "ep-show-s1e1",
        "language": "en",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Pilot"
    assert data["content_group"] == "ep-show-s1e1"


def test_episode_content_group_language_uniqueness(client, editor_token):
    show = _create_show(client, editor_token, "unique-show").json()
    season = _create_season(client, editor_token, show["id"]).json()
    client.post("/episodes", headers=auth_header(editor_token), json={
        "show_id": show["id"],
        "season_id": season["id"],
        "number": 1,
        "title": "Ep 1",
        "content_group": "unique-cg",
        "language": "en",
    })
    resp = client.post("/episodes", headers=auth_header(editor_token), json={
        "show_id": show["id"],
        "season_id": season["id"],
        "number": 2,
        "title": "Ep 2",
        "content_group": "unique-cg",
        "language": "en",
    })
    assert resp.status_code == 400


def test_editor_cannot_publish(client, editor_token, db):
    from app.models import User
    from app.core.security import hash_password
    user = User(username="onlyeditor", password_hash=hash_password("x"), role="editor")
    db.add(user)
    db.commit()
    resp = client.post("/admin/catalog/publish", headers=auth_header(editor_token))
    assert resp.status_code == 403


def test_admin_can_publish(client, admin_token, db):
    from app.models import Show, User
    from app.core.security import hash_password

    user = db.query(User).filter(User.username == "testadmin").first()
    user.role = "admin"
    db.commit()

    # Create a published show with section
    show = Show(title="Pub Show", slug="pub-show", section="Entertainment", status="published")
    db.add(show)
    db.commit()
    db.refresh(show)

    resp = client.post("/admin/catalog/publish", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
