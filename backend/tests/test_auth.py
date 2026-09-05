def test_login_admin(client, admin_user):
    resp = client.post("/auth/login", json={"username": "testadmin", "password": "testpass"})
    print(f"\nDEBUG response: {resp.status_code} {resp.text}")
    assert resp.status_code == 200


def test_login_editor(client, editor_user):
    resp = client.post("/auth/login", json={"username": "testeditor", "password": "testpass"})
    print(f"\nDEBUG response: {resp.status_code} {resp.text}")
    assert resp.status_code == 200


def test_login_invalid(client):
    resp = client.post("/auth/login", json={"username": "nobody", "password": "wrong"})
    print(f"\nDEBUG response: {resp.status_code} {resp.text}")
    assert resp.status_code == 401


def test_me(client, admin_user, admin_token):
    resp = client.get("/auth/me", headers=auth_header(admin_token))
    print(f"\nDEBUG response: {resp.status_code} {resp.text}")
    assert resp.status_code == 200


def test_unauthorized(client):
    resp = client.get("/shows")
    assert resp.status_code == 403

from tests.conftest import auth_header
