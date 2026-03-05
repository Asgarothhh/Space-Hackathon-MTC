"""
Fixtures для изолированного тестирования бэкенда.

Окружение 1 — Backend-only:
  - PostgreSQL (тестовая БД mts_test)
  - Mock Docker вместо реального
  - TestClient для HTTP-тестов
"""

import getpass
import os
import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

os.environ["TESTING"] = "1"

_db_user = os.getenv("POSTGRES_TEST_USER") or os.getenv("POSTGRES_USER") or getpass.getuser()
_db_password = os.getenv("POSTGRES_TEST_PASSWORD") or os.getenv("POSTGRES_PASSWORD") or ""
_db_host = os.getenv("POSTGRES_TEST_HOST") or os.getenv("POSTGRES_HOST") or "localhost"
_db_port = os.getenv("POSTGRES_TEST_PORT") or os.getenv("POSTGRES_PORT") or "5432"
_db_name = os.getenv("POSTGRES_TEST_DB") or os.getenv("POSTGRES_DB") or "mts_test"

os.environ["POSTGRES_USER"] = _db_user
os.environ["POSTGRES_PASSWORD"] = _db_password
os.environ["POSTGRES_HOST"] = _db_host
os.environ["POSTGRES_PORT"] = _db_port
os.environ["POSTGRES_DB"] = _db_name
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-tests")

if _db_password:
    TEST_DB_URL = f"postgresql://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"
else:
    TEST_DB_URL = f"postgresql://{_db_user}@{_db_host}:{_db_port}/{_db_name}"

from tests.mocks.docker_mock import MockDockerClient

_test_engine = create_engine(TEST_DB_URL, echo=False)

import backend.models.db as db_module

db_module.engine = _test_engine
db_module.SessionLocal = sessionmaker(bind=_test_engine, autoflush=False, autocommit=False)

SCHEMAS = [
    "auth_service",
    "project_service",
    "compute_service",
    "network_service",
    "orchestrator",
]

with _test_engine.begin() as conn:
    for schema in SCHEMAS:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

import backend.models.auth  # noqa: F401
import backend.models.projects  # noqa: F401
import backend.models.compute  # noqa: F401
import backend.models.network  # noqa: F401
import backend.models.orchestrator  # noqa: F401
from backend.models.db import Base

Base.metadata.drop_all(bind=_test_engine)
Base.metadata.create_all(bind=_test_engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    """Очищает все таблицы после каждого теста."""
    yield
    with _test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture()
def db_session() -> Session:
    session = db_module.SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def mock_docker():
    client = MockDockerClient()
    with patch("docker.from_env", return_value=client):
        yield client


@pytest.fixture()
def app(mock_docker):
    """FastAPI TestClient с подменёнными зависимостями."""
    from backend.main import app as fastapi_app
    from backend.routers.dependencies import get_db
    from backend.routers.admin import get_db as admin_get_db

    def _override_get_db():
        db = db_module.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    fastapi_app.dependency_overrides[admin_get_db] = _override_get_db

    yield fastapi_app

    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def client(app):
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def registered_user(client) -> dict:
    """Создаёт пользователя и возвращает dict с email, password, token, user_id."""
    email = f"testuser-{uuid.uuid4().hex[:8]}@test.com"
    password = "testpassword123"

    resp = client.post("/user/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    user_data = resp.json()

    resp = client.post("/user/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token_data = resp.json()

    return {
        "email": email,
        "password": password,
        "user_id": user_data["id"],
        "token": token_data["access_token"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"},
    }


@pytest.fixture()
def admin_user(client, db_session) -> dict:
    """Создаёт admin-пользователя."""
    email = f"admin-{uuid.uuid4().hex[:8]}@test.com"
    password = "adminpassword123"

    resp = client.post("/user/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    user_data = resp.json()

    from backend.models.auth import User
    user = db_session.query(User).filter(User.id == uuid.UUID(user_data["id"])).first()
    if user:
        user.role = "admin"
        db_session.commit()

    resp = client.post("/user/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token_data = resp.json()

    return {
        "email": email,
        "password": password,
        "user_id": user_data["id"],
        "token": token_data["access_token"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"},
    }
