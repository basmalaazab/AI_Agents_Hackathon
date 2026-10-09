"""
conftest.py — patches JSONB → JSON before any model imports happen,
so integration tests work with SQLite (in-memory) without PostgreSQL.
"""
import os

# Must be set before any app imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ["OPENAI_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""

# Patch JSONB to JSON for SQLite compatibility
from sqlalchemy import JSON
import sqlalchemy.dialects.postgresql as pg_dialect

class _SQLiteCompatibleJSON(JSON):
    """JSONB replacement that works with SQLite for unit/integration tests."""
    pass

# Replace before models are loaded
pg_dialect.JSONB = _SQLiteCompatibleJSON  # type: ignore

import uuid
import pytest
from fastapi import Depends
from sqlalchemy.orm import Session

from app.main import app
from app.api.auth import get_current_user, require_manager
from app.database import get_db
from app.models.auth import AppUser
from app.models.data_source import DataSource

_TEST_WORKSPACE_ID = uuid.uuid4()
_TEST_USER = AppUser(
    id=uuid.uuid4(),
    email="test_owner@example.com",
    full_name="Test Owner",
    hashed_password="fake",
    role="business_owner",
    workspace_id=_TEST_WORKSPACE_ID,
)


@pytest.fixture(autouse=True)
def setup_mock_auth_for_tests():
    def _mock_user(db: Session = Depends(get_db)):
        sources = db.query(DataSource).all()
        db.info["workspace_id"] = _TEST_WORKSPACE_ID
        db.info["skip_workspace_scope"] = True
        db.info["workspace_source_names"] = tuple(s.name for s in sources)
        db.info["workspace_source_labels"] = {s.name: (s.display_name or s.name) for s in sources}
        db.info["workspace_source_ids"] = tuple(s.id for s in sources)
        db.info["app_user_id"] = _TEST_USER.id
        return _TEST_USER

    def _mock_manager(user: AppUser = Depends(_mock_user)):
        return user

    app.dependency_overrides[get_current_user] = _mock_user
    app.dependency_overrides[require_manager] = _mock_manager
    yield
    app.dependency_overrides[get_current_user] = _mock_user
    app.dependency_overrides[require_manager] = _mock_manager
