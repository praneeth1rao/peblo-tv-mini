"""Shared test fixtures."""

import os
import tempfile

# Set test env vars BEFORE any app imports
_STORAGE = tempfile.mkdtemp()
_TEST_DB = tempfile.mktemp(suffix=".db")
os.environ["STORAGE_PATH"] = _STORAGE
os.environ["CATALOGUE_DIR"] = os.path.join(_STORAGE, "catalogue")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

test_engine = create_engine(
    f"sqlite:///{_TEST_DB}",
    connect_args={"check_same_thread": False},
)
TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

# Monkey-patch session module
import app.db.session as _session_module
_session_module.engine = test_engine
_session_module.SessionLocal = TestSession


def _test_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


# Replace get_db in the session module itself
_session_module.get_db = _test_get_db

from app.db.session import Base
from app.main import app
from app.models import User
from app.core.security import hash_password, create_token
from starlette.testclient import TestClient

# Create all tables once
Base.metadata.create_all(bind=test_engine)


@pytest.fixture(autouse=True)
def _setup_teardown():
    """Reset tables between tests."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def admin_user(db):
    user = User(username="testadmin", password_hash=hash_password("testpass"), role="admin")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def editor_user(db):
    user = User(username="testeditor", password_hash=hash_password("testpass"), role="editor")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def admin_token(admin_user):
    return create_token(admin_user.username, admin_user.role)


@pytest.fixture
def editor_token(editor_user):
    return create_token(editor_user.username, editor_user.role)


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
