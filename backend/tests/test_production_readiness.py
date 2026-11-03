import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware

from app.core.database import get_db
from app.main import app, create_app

STRONG_TEST_SECRET = "GZ4Vf2xq8pN1mR7sK3dH9wQ6bT5yC0uL4aE8jF2vM1nP7zX9kB6cD3hS5rW0qA"


class _HealthySession:
    def execute(self, _statement):
        return 1


class _UnavailableSession:
    def execute(self, _statement):
        raise SQLAlchemyError("private database connection detail")


def test_health_endpoints_distinguish_liveness_and_readiness():
    app.dependency_overrides[get_db] = lambda: _HealthySession()
    try:
        with TestClient(app) as client:
            assert client.get("/health/live").json() == {"status": "ok"}
            assert client.get("/health/ready").json() == {"status": "ready"}
    finally:
        app.dependency_overrides.clear()


def test_readiness_returns_generic_503_without_database_details():
    app.dependency_overrides[get_db] = lambda: _UnavailableSession()
    try:
        with TestClient(app) as client:
            response = client.get("/health/ready")
        assert response.status_code == 503
        assert response.json() == {"detail": "Database unavailable"}
        assert "private database connection detail" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_production_disables_docs_and_localhost_cors_regex(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", '["https://app.example.invalid"]')
    monkeypatch.setenv("JWT_SECRET", STRONG_TEST_SECRET)

    production_app = create_app()

    assert production_app.docs_url is None
    assert production_app.redoc_url is None
    assert production_app.openapi_url is None
    cors = next(
        middleware
        for middleware in production_app.user_middleware
        if middleware.cls is CORSMiddleware
    )
    assert cors.kwargs["allow_origins"] == ["https://app.example.invalid"]
    assert cors.kwargs["allow_origin_regex"] is None
    assert "*" not in cors.kwargs["allow_methods"]
    assert "*" not in cors.kwargs["allow_headers"]


@pytest.mark.parametrize(
    ("origins", "secret"),
    [
        ('["*"]', STRONG_TEST_SECRET),
        ('["http://app.example.invalid"]', STRONG_TEST_SECRET),
        ('["https://app.example.invalid/path"]', STRONG_TEST_SECRET),
        ('["https://app.example.invalid"]', "replace-with-a-real-secret"),
    ],
)
def test_production_rejects_wildcard_or_non_https_origins_and_weak_secret(
    monkeypatch, origins, secret
):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", origins)
    monkeypatch.setenv("JWT_SECRET", secret)

    with pytest.raises(RuntimeError):
        create_app()


def test_production_rejects_debug_mode(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", '["https://app.example.invalid"]')
    monkeypatch.setenv("JWT_SECRET", STRONG_TEST_SECRET)
    monkeypatch.setenv("DEBUG", "true")

    with pytest.raises(RuntimeError, match="DEBUG"):
        create_app()
