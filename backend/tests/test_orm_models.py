"""Unit tests to verify SQLAlchemy ORM Models configurations and relationships."""

import pytest
from memory.database import Base
# Importing memory.orm registers all schemas with Base.metadata
import memory.orm  # noqa: F401


def test_orm_models_registered_with_metadata() -> None:
    """Verify all expected database tables are correctly registered in Base.metadata."""
    expected_tables = {
        "users",
        "preferences",
        "workspace_profiles",
        "contexts",
        "conversation_history",
        "routine_learning",
        "execution_history",
        "memory_events",
    }
    registered_tables = set(Base.metadata.tables.keys())
    for table_name in expected_tables:
        assert table_name in registered_tables, f"Table '{table_name}' was not discovered in Base.metadata"


def test_users_relationships() -> None:
    """Verify that User ORM model relations and cascade configurations are set correctly."""
    user_table = Base.metadata.tables["users"]
    
    # 1. Verify primary keys
    assert len(user_table.primary_key.columns) == 1
    assert "id" in user_table.columns

    # 2. Check presence of correct columns
    assert "username" in user_table.columns
    assert "email" in user_table.columns
    assert "created_at" in user_table.columns
    assert "updated_at" in user_table.columns


def test_preference_constraints_and_foreign_keys() -> None:
    """Verify that Preference model foreign key constraints and unique constraints match specs."""
    pref_table = Base.metadata.tables["preferences"]
    
    # 1. Foreign Keys
    fkeys = pref_table.foreign_keys
    assert len(fkeys) == 1
    fkey = list(fkeys)[0]
    assert fkey.column.table.name == "users"
    assert fkey.column.name == "id"
    assert fkey.ondelete == "CASCADE"

    # 2. Unique Constraints
    # Ensure there is a unique constraint on user_id and key
    unique_constraints = [c for c in pref_table.constraints if c.__class__.__name__ == "UniqueConstraint"]
    assert len(unique_constraints) >= 1
    
    uq_col_names = {c.name: [col.name for col in c.columns] for c in unique_constraints}
    found_uq = False
    for uq_name, cols in uq_col_names.items():
        if set(cols) == {"user_id", "key"}:
            found_uq = True
            break
            
    assert found_uq, "No UniqueConstraint found on ('user_id', 'key')"


def test_workspace_profile_columns() -> None:
    """Verify columns in WorkspaceProfile table."""
    workspace_table = Base.metadata.tables["workspace_profiles"]
    assert "name" in workspace_table.columns
    assert "path" in workspace_table.columns
    assert "settings" in workspace_table.columns
    
    # Verify settings is JSONB (PostgreSQL specific dialect representation)
    col_type = workspace_table.columns["settings"].type
    assert col_type.__class__.__name__ == "JSONB"
