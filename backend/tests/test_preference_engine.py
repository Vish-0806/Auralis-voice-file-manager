"""Unit tests for the User Preference Engine."""

# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker, Session
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.compiler import compiles
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import JSONB
# pyrefly: ignore [missing-import]
from memory.database import Base
# pyrefly: ignore [missing-import]
from memory.exceptions import RecordNotFoundError
# pyrefly: ignore [missing-import]
from memory.repository.preference_repository import PreferenceRepository
from memory.preferences import (
    PreferenceService,
    PreferenceEngine,
    PreferenceCache,
    PreferenceValidator,
    InvalidPreferenceError,
    DuplicatePreferenceError,
)



@pytest.fixture(scope="module")
def db_engine():
    """Provides a SQLite in-memory engine for preference engine testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine) -> Session:
    """Provides a transactional database Session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session_local = sessionmaker(bind=connection)
    session = session_local()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def preference_engine(db_session: Session) -> PreferenceEngine:
    """Fixture providing a configured PreferenceEngine."""
    repository = PreferenceRepository(db_session)
    cache = PreferenceCache(ttl_seconds=5)
    return PreferenceEngine(repository=repository, cache=cache)


def test_validator_raises_on_invalid_inputs() -> None:
    """Verify that PreferenceValidator validates categories, keys, and types correctly."""
    validator = PreferenceValidator()

    # Invalid Category
    with pytest.raises(InvalidPreferenceError) as exc:
        validator.validate("invalid_cat", "theme", "dark")
    assert "Invalid preference category" in str(exc.value)

    # Invalid Key
    with pytest.raises(InvalidPreferenceError) as exc:
        validator.validate("ide", "invalid_key", "vs-dark")
    assert "Invalid key" in str(exc.value)

    # Invalid Type (int expected, got str)
    with pytest.raises(InvalidPreferenceError) as exc:
        validator.validate("ide", "font_size", "fourteen")
    assert "Invalid type" in str(exc.value)

    # Invalid Type (bool expected, got int)
    with pytest.raises(InvalidPreferenceError) as exc:
        validator.validate("voice", "tts_enabled", 1)
    assert "Invalid type" in str(exc.value)

    # Forgiving type check (float accepts int)
    validator.validate("voice", "speech_rate", 2)  # Should pass without error


def test_preference_cache_operations() -> None:
    """Verify cache sets, gets, invalidates, and clear logic."""
    cache = PreferenceCache(ttl_seconds=1)

    # Initially empty
    assert cache.get(user_id=1, category="ide", key="theme") is None

    # Set and Get
    cache.set(user_id=1, category="ide", key="theme", value="synthwave")
    assert cache.get(user_id=1, category="ide", key="theme") == "synthwave"

    # Invalidate
    cache.invalidate(user_id=1, category="ide", key="theme")
    assert cache.get(user_id=1, category="ide", key="theme") is None

    # Clear user cache
    cache.set(user_id=1, category="ide", key="theme", value="vs-dark")
    cache.set(user_id=1, category="voice", key="speech_rate", value=1.2)
    cache.clear(user_id=1)
    assert cache.get(user_id=1, category="ide", key="theme") is None
    assert cache.get(user_id=1, category="voice", key="speech_rate") is None


def test_preference_engine_crud(preference_engine: PreferenceEngine) -> None:
    """Verify preference creation, read, update, and deletion flow."""
    user_id = 99

    # 1. Read default values when no record exists in DB
    default_theme = preference_engine.get_preference(user_id, "ide", "theme")
    assert default_theme == "vs-dark"

    # 2. Create a preference
    saved = preference_engine.create_preference(user_id, "ide", "theme", "synthwave")
    assert saved.id is not None
    assert saved.user_id == user_id

    # Retrieve from engine (should now be the custom value, not default)
    assert preference_engine.get_preference(user_id, "ide", "theme") == "synthwave"

    # 3. Prevent duplicate creation
    with pytest.raises(DuplicatePreferenceError):
        preference_engine.create_preference(user_id, "ide", "theme", "vs-dark")

    # 4. Update
    updated = preference_engine.update_preference(user_id, "ide", "theme", "monokai")
    assert updated.value.get("value") == "monokai"
    assert preference_engine.get_preference(user_id, "ide", "theme") == "monokai"

    # 5. Delete
    deleted = preference_engine.delete_preference(user_id, "ide", "theme")
    assert deleted is True

    # After deletion, read falls back to default
    assert preference_engine.get_preference(user_id, "ide", "theme") == "vs-dark"


def test_list_preferences_merged_with_defaults(preference_engine: PreferenceEngine) -> None:
    """Verify listing preferences overlays database values onto schema defaults."""
    user_id = 100

    # Retrieve defaults initially
    ide_prefs = preference_engine.list_preferences(user_id, "ide")
    assert ide_prefs == {"theme": "vs-dark", "font_size": 14, "tab_size": 4}

    # Set custom value in DB
    preference_engine.create_preference(user_id, "ide", "font_size", 18)

    # Check merged results
    ide_prefs_updated = preference_engine.list_preferences(user_id, "ide")
    assert ide_prefs_updated == {"theme": "vs-dark", "font_size": 18, "tab_size": 4}

    # List all categories
    all_prefs = preference_engine.list_preferences(user_id)
    assert "ide" in all_prefs
    assert all_prefs["ide"]["font_size"] == 18
    assert all_prefs["theme"]["mode"] == "dark"  # default


def test_reset_preferences(preference_engine: PreferenceEngine) -> None:
    """Verify resetting preferences clears DB entries and invalidates cache."""
    user_id = 101

    preference_engine.create_preference(user_id, "ide", "font_size", 20)
    preference_engine.create_preference(user_id, "theme", "mode", "light")

    # Verify customized
    assert preference_engine.get_preference(user_id, "ide", "font_size") == 20
    assert preference_engine.get_preference(user_id, "theme", "mode") == "light"

    # Reset single category
    preference_engine.reset_preferences(user_id, "ide")
    assert preference_engine.get_preference(user_id, "ide", "font_size") == 14  # reset to default
    assert preference_engine.get_preference(user_id, "theme", "mode") == "light"  # untouched

    # Reset all
    preference_engine.reset_preferences(user_id)
    assert preference_engine.get_preference(user_id, "theme", "mode") == "dark"  # reset to default


def test_preference_service_delegates_successfully(db_session: Session) -> None:
    """Verify that PreferenceService public methods delegate to the engine correctly."""
    repository = PreferenceRepository(db_session)
    engine = PreferenceEngine(repository)
    service = PreferenceService(engine)

    user_id = 102

    # Verify set (auto creates)
    saved = service.set(user_id, "ide", "theme", "cyberpunk")
    assert saved.key == "ide:theme"
    assert service.get(user_id, "ide", "theme") == "cyberpunk"

    # Verify set (auto updates)
    updated = service.set(user_id, "ide", "theme", "vs-dark")
    assert service.get(user_id, "ide", "theme") == "vs-dark"

    # List
    assert service.list(user_id, "ide")["theme"] == "vs-dark"

    # Delete
    assert service.delete(user_id, "ide", "theme") is True
    assert service.get(user_id, "ide", "theme") == "vs-dark"  # default
