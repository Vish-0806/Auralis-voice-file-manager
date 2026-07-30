"""Unit tests for the Auralis Memory Repository layer."""
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
from memory.database import Base
from memory.models.domain_models import UserDomain, PreferenceDomain
from memory.repository.repository_factory import RepositoryFactory
from memory.repository.user_repository import UserRepository
from memory.repository.preference_repository import PreferenceRepository



@pytest.fixture
def db_session() -> Session:
    """Fixture providing a transactional SQLite in-memory database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()


def test_repository_factory_resolution(db_session: Session) -> None:
    """Verify that RepositoryFactory resolves all specialized repositories correctly."""
    factory = RepositoryFactory(db_session)
    
    assert isinstance(factory.get_user_repository(), UserRepository)
    assert isinstance(factory.get_preference_repository(), PreferenceRepository)


def test_user_repository_crud(db_session: Session) -> None:
    """Verify CRUD and specialized lookups on UserRepository."""
    repo = UserRepository(db_session)

    # 1. Create
    user_domain = UserDomain(username="test_user", email="test@example.com")
    created_user = repo.create(user_domain)
    
    assert created_user.id is not None
    assert created_user.username == "test_user"
    assert created_user.email == "test@example.com"

    # 2. Get by ID
    retrieved = repo.get_by_id(created_user.id)
    assert retrieved is not None
    assert retrieved.username == "test_user"

    # 3. Get by Username
    by_name = repo.get_by_username("test_user")
    assert by_name is not None
    assert by_name.id == created_user.id

    # 4. Count and Exists
    assert repo.count(username="test_user") == 1
    assert repo.exists(username="test_user") is True
    assert repo.exists(username="nonexistent") is False

    # 5. List and Search
    all_users = repo.list_all()
    assert len(all_users) == 1
    
    search_result = repo.search({"username": "test_user"})
    assert len(search_result) == 1
    assert search_result[0].id == created_user.id

    # 6. Update
    created_user.email = "updated@example.com"
    updated_user = repo.update(created_user.id, created_user)
    assert updated_user is not None
    assert updated_user.email == "updated@example.com"

    # 7. Delete
    deleted = repo.delete(created_user.id)
    assert deleted is True
    assert repo.get_by_id(created_user.id) is None
    assert repo.count() == 0


def test_preference_repository_crud(db_session: Session) -> None:
    """Verify CRUD and user-preference constraints on PreferenceRepository."""
    factory = RepositoryFactory(db_session)
    user_repo = factory.get_user_repository()
    pref_repo = factory.get_preference_repository()

    # Create parent user
    user = user_repo.create(UserDomain(username="preference_owner"))

    # 1. Create Preference
    pref = PreferenceDomain(
        user_id=user.id,
        key="theme",
        value={"mode": "dark", "fontSize": 14}
    )
    created_pref = pref_repo.create(pref)
    assert created_pref.id is not None
    assert created_pref.key == "theme"
    assert created_pref.value["mode"] == "dark"

    # 2. Get by User and Key
    retrieved = pref_repo.get_by_user_and_key(user.id, "theme")
    assert retrieved is not None
    assert retrieved.id == created_pref.id
    assert retrieved.value["fontSize"] == 14

    # 3. Update Preference
    created_pref.value["fontSize"] = 16
    updated = pref_repo.update(created_pref.id, created_pref)
    assert updated is not None
    assert updated.value["fontSize"] == 16
