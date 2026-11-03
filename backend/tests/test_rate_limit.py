from fastapi.testclient import TestClient

from app.core.rate_limit import FixedWindowRateLimiter
from app.main import create_app

STRONG_TEST_SECRET = "GZ4Vf2xq8pN1mR7sK3dH9wQ6bT5yC0uL4aE8jF2vM1nP7zX9kB6cD3hS5rW0qA"


def test_fixed_window_allows_limit_then_returns_retry_after_and_resets():
    limiter = FixedWindowRateLimiter()

    assert limiter.check("login:192.0.2.10", 2, 60, now=100) == (True, 0)
    assert limiter.check("login:192.0.2.10", 2, 60, now=101) == (True, 0)
    allowed, retry_after = limiter.check("login:192.0.2.10", 2, 60, now=102)

    assert allowed is False
    assert retry_after == 58
    assert limiter.check("login:192.0.2.10", 2, 60, now=160) == (True, 0)


def test_public_login_limit_returns_safe_429_and_does_not_trust_forwarded_header(
    monkeypatch,
):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", '["https://app.example.invalid"]')
    monkeypatch.setenv("JWT_SECRET", STRONG_TEST_SECRET)
    monkeypatch.setenv("RATE_LIMIT_LOGIN_PER_MINUTE", "2")
    client = TestClient(create_app())

    try:
        headers = {
            "Origin": "https://app.example.invalid",
            "X-Forwarded-For": "198.51.100.10",
        }
        first = client.post("/auth/jwt/login", headers=headers)
        second = client.post("/auth/jwt/login", headers=headers)
        third = client.post(
            "/auth/jwt/login",
            headers={**headers, "X-Forwarded-For": "198.51.100.11"},
        )

        assert first.status_code == second.status_code == 422
        assert third.status_code == 429
        assert third.json() == {
            "detail": "Too many requests. Please try again later."
        }
        assert int(third.headers["Retry-After"]) > 0
        assert third.headers["Access-Control-Allow-Origin"] == (
            "https://app.example.invalid"
        )
    finally:
        client.close()


def test_rate_limit_configuration_must_be_positive(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("RATE_LIMIT_CATALOG_PER_MINUTE", "0")

    try:
        create_app()
    except RuntimeError as error:
        assert "RATE_LIMIT_CATALOG_PER_MINUTE" in str(error)
    else:
        raise AssertionError("Invalid rate-limit configuration was accepted")
