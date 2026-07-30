"""Pytest configuration and shared fixtures for Auralis backend tests."""

# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]  
from sqlalchemy.ext.compiler import compiles
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import JSONB


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    """Compiles JSONB columns as JSON under SQLite to support developer testing."""
    return "JSON"
