from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from backend.app.infrastructure.database import get_session
from backend.app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Business Workflow Automation Platform"}


def test_database_health() -> None:
    mock_session = AsyncMock()
    app.dependency_overrides[get_session] = lambda: mock_session

    try:
        response = client.get("/health/db")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ok",
    }
    mock_session.execute.assert_awaited_once()


def test_database_health_unavailable() -> None:
    mock_session = AsyncMock()
    mock_session.execute.side_effect = SQLAlchemyError("Database error")
    app.dependency_overrides[get_session] = lambda: mock_session

    try:
        response = client.get("/health/db")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database unavailable",
    }
