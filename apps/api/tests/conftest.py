from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_tmp_dir = tempfile.mkdtemp(prefix="ecosynapse_test_")
_db_path = Path(_tmp_dir) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path.as_posix()}"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "hashing"

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
