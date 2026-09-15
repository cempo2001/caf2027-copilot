"""
Smoke test za Korak 2 skeleton — dokazuje da se aplikacija podiže,
config se validno učitava i health endpoint radi. Ne zahtijeva bazu.

Puni RLS/Approved Lock testovi (test_rls_isolation.py,
test_approved_lock.py) dolaze u Koraku 4, kad modeli postoje — vidi
docs/ARCHITECTURE.md Sekcija 6.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://app_user:test@localhost:5432/caf2027")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ROOT_USER", "test")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "test")
os.environ.setdefault("JWT_SECRET_KEY", "a" * 32)

from fastapi.testclient import TestClient  # noqa: E402

from caf.main import create_app  # noqa: E402


def test_health_endpoint_returns_ok() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_settings_reject_missing_required_fields() -> None:
    from pydantic import ValidationError

    from caf.core.config import Settings

    os.environ.pop("JWT_SECRET_KEY", None)
    try:
        with __import__("pytest").raises(ValidationError):
            Settings(_env_file=None, database_url="postgresql+asyncpg://x/y", redis_url="redis://x")
    finally:
        os.environ["JWT_SECRET_KEY"] = "a" * 32
