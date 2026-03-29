from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_user_repository
from app.main import app
from app.models.user import Role, User


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_me_without_token(client: TestClient) -> None:
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_me_with_mock_user(client: TestClient) -> None:
    role = Role(id=1, code="viewer", name="Viewer", description=None)
    user = User(
        id=1,
        email="u@test.local",
        password_hash="x",
        full_name="Test",
        is_active=True,
    )
    user.roles = [role]

    app.dependency_overrides[get_current_user] = lambda: user
    try:
        r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer fake"})
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == "u@test.local"
        assert body["roles"][0]["code"] == "viewer"
    finally:
        app.dependency_overrides.clear()


def test_login_invalid_credentials(client: TestClient) -> None:
    mock_repo = MagicMock()
    mock_repo.get_by_email.return_value = None
    app.dependency_overrides[get_user_repository] = lambda: mock_repo
    try:
        r = client.post("/api/v1/auth/login", json={"email": "nope@test.local", "password": "wrong"})
        assert r.status_code == 401
    finally:
        app.dependency_overrides.clear()
