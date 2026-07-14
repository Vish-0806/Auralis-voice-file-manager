"""Unit tests for the Auralis PostgreSQL Database Infrastructure layer."""

import os
from unittest.mock import patch, MagicMock
import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from memory.database.config import DBConfig
from memory.database.database import get_engine
from memory.database.session import get_db


def test_database_config_env_loading() -> None:
    """Test loading and validating database configuration from env."""
    custom_env = {
        "DATABASE_HOST": "test-host",
        "DATABASE_PORT": "9999",
        "DATABASE_NAME": "test-db",
        "DATABASE_USER": "test-user",
        "DATABASE_PASSWORD": "test-password",
        "DATABASE_URL": "postgresql+psycopg://custom:url@localhost:5432/db",
    }
    with patch.dict(os.environ, custom_env):
        config = DBConfig(
            host=os.getenv("DATABASE_HOST"),
            port=int(os.getenv("DATABASE_PORT")),
            name=os.getenv("DATABASE_NAME"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            url=os.getenv("DATABASE_URL"),
        )
        assert config.host == "test-host"
        assert config.port == 9999
        assert config.name == "test-db"
        assert config.user == "test-user"
        assert config.password == "test-password"
        assert config.url == "postgresql+psycopg://custom:url@localhost:5432/db"


def test_database_config_default_url_construction() -> None:
    """Test dynamic connection URL construction when DATABASE_URL is not provided."""
    config = DBConfig(
        host="myhost",
        port=5432,
        name="mydb",
        user="myuser",
        password="mypassword",
        url=None,
    )
    assert config.url == "postgresql+psycopg://myuser:mypassword@myhost:5432/mydb"


def test_engine_singleton() -> None:
    """Test that get_engine returns a singleton Engine instance."""
    engine1 = get_engine()
    engine2 = get_engine()
    assert isinstance(engine1, Engine)
    assert engine1 is engine2


def test_get_db_session_lifecycle() -> None:
    """Test the session generator yield, close, and error rollback behaviors."""
    # We mock SessionLocal to assert lifecycle methods are called correctly
    mock_session = MagicMock(spec=Session)
    
    with patch("memory.database.session.SessionLocal", return_value=mock_session):
        # 1. Test successful path
        generator = get_db()
        session = next(generator)
        assert session is mock_session
        
        # Verify finally block is hit when generator terminates
        try:
            next(generator)
        except StopIteration:
            pass
        mock_session.close.assert_called_once()
        mock_session.rollback.assert_not_called()

        # Reset mocks
        mock_session.reset_mock()

        # 2. Test error rollback path
        generator_err = get_db()
        session_err = next(generator_err)
        assert session_err is mock_session
        
        with pytest.raises(ValueError, match="Database Error"):
            generator_err.throw(ValueError("Database Error"))
            
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
