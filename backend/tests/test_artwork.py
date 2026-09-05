import io
from PIL import Image

from tests.conftest import auth_header


def _make_image(width: int, height: int, fmt="PNG") -> bytes:
    img = Image.new("RGB", (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_upload_valid_poster(client, editor_token):
    # Create a show first
    show = client.post("/shows", headers=auth_header(editor_token), json={
        "title": "Art Show", "slug": "art-show", "section": "Ent",
    }).json()

    img_data = _make_image(600, 900)
    resp = client.post("/artwork", headers=auth_header(editor_token), data={
        "artwork_type": "poster",
        "show_id": show["id"],
    }, files={"file": ("poster.png", io.BytesIO(img_data), "image/png")})
    assert resp.status_code == 201
    assert resp.json()["width"] == 600
    assert resp.json()["height"] == 900


def test_upload_valid_banner(client, editor_token):
    show = client.post("/shows", headers=auth_header(editor_token), json={
        "title": "Banner Show", "slug": "banner-show", "section": "Ent",
    }).json()
    img_data = _make_image(1280, 720)
    resp = client.post("/artwork", headers=auth_header(editor_token), data={
        "artwork_type": "banner",
        "show_id": show["id"],
    }, files={"file": ("banner.png", io.BytesIO(img_data), "image/png")})
    assert resp.status_code == 201


def test_upload_valid_thumbnail(client, editor_token):
    show = client.post("/shows", headers=auth_header(editor_token), json={
        "title": "Thumb Show", "slug": "thumb-show", "section": "Ent",
    }).json()
    img_data = _make_image(640, 360)
    resp = client.post("/artwork", headers=auth_header(editor_token), data={
        "artwork_type": "thumbnail",
        "show_id": show["id"],
    }, files={"file": ("thumb.png", io.BytesIO(img_data), "image/png")})
    assert resp.status_code == 201


def test_upload_wrong_aspect_ratio(client, editor_token):
    show = client.post("/shows", headers=auth_header(editor_token), json={
        "title": "Bad Ratio", "slug": "bad-ratio", "section": "Ent",
    }).json()
    # Poster should be 2:3 ratio, giving it 16:9 instead
    img_data = _make_image(1280, 720)
    resp = client.post("/artwork", headers=auth_header(editor_token), data={
        "artwork_type": "poster",
        "show_id": show["id"],
    }, files={"file": ("bad.png", io.BytesIO(img_data), "image/png")})
    assert resp.status_code == 400
    assert "aspect ratio" in resp.json()["detail"].lower()


def test_upload_oversized_file(client, editor_token):
    show = client.post("/shows", headers=auth_header(editor_token), json={
        "title": "Big File", "slug": "big-file", "section": "Ent",
    }).json()
    # Create a 300KB image
    img = Image.new("RGB", (2000, 2000), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()
    # If it's under 200KB, pad it
    if len(data) < 200 * 1024:
        data = data + b"\x00" * (201 * 1024 - len(data))
    resp = client.post("/artwork", headers=auth_header(editor_token), data={
        "artwork_type": "poster",
        "show_id": show["id"],
    }, files={"file": ("big.png", io.BytesIO(data), "image/png")})
    assert resp.status_code == 400
    assert "200 KB" in resp.json()["detail"]


def test_invalid_artwork_type(client, editor_token):
    show = client.post("/shows", headers=auth_header(editor_token), json={
        "title": "Invalid Type", "slug": "inv-type", "section": "Ent",
    }).json()
    img_data = _make_image(600, 900)
    resp = client.post("/artwork", headers=auth_header(editor_token), data={
        "artwork_type": "invalid",
        "show_id": show["id"],
    }, files={"file": ("img.png", io.BytesIO(img_data), "image/png")})
    assert resp.status_code == 400
