"""
conftest.py — patches JSONB → JSON before any model imports happen,
so integration tests work with SQLite (in-memory) without PostgreSQL.
"""
import os

# Must be set before any app imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# Patch JSONB to JSON for SQLite compatibility
from sqlalchemy import JSON
import sqlalchemy.dialects.postgresql as pg_dialect

class _SQLiteCompatibleJSON(JSON):
    """JSONB replacement that works with SQLite for unit/integration tests."""
    pass

# Replace before models are loaded
pg_dialect.JSONB = _SQLiteCompatibleJSON  # type: ignore
