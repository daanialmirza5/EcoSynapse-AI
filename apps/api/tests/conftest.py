from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

## Respect a DATABASE_URL the caller already set (e.g. CI's Postgres service
# container job) rather than always overwriting it -- otherwise this fixture
# would silently defeat any attempt to run the suite against real Postgres,
# which is exactly how a Postgres-only bug (VARCHAR column too narrow;
# SQLite doesn't enforce declared lengths) previously went undetected by
# this suite. Only default to an isolated temp SQLite file when nothing was
# already configured, so plain local `pytest` runs stay zero-setup.
if not os.environ.get("DATABASE_URL"):
    _tmp_dir = tempfile.mkdtemp(prefix="ecosynapse_test_")
    _db_path = Path(_tmp_dir) / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{_db_path.as_posix()}"
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("EMBEDDING_PROVIDER", "hashing")

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.knowledge.seed import seed_all  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_all(db)
    db.close()
    yield


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
