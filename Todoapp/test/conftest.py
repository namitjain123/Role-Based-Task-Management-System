import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from types import SimpleNamespace

from Todoapp.main import app
from Todoapp.database import Base
from Todoapp.models import Todos
from Todoapp.routers.todos import get_db, get_current_user

SQLALCHEMY_DATABASE_URL = "sqlite:///./testdb.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables once for the test DB
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    # Must return an object (not dict) because your code uses current_user.id
    return SimpleNamespace(id=1, username="namit", role="admin")


@pytest.fixture(scope="session")
def client():
    # Override dependencies once per test session
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    return TestClient(app)


@pytest.fixture
def db():
    """Gives a DB session for direct DB checks in tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def as_non_admin():
    """
    Temporarily makes the fake logged-in user a non-admin (role='user'),
    for the duration of a single test. Every other test runs as the default
    fake admin (see override_get_current_user above) - this fixture is how
    a test proves an endpoint actually REJECTS a non-admin, instead of just
    assuming it does because it looks right.
    """
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=2, username="bob", role="user"
    )
    yield
    # Restore the default admin override so later tests aren't affected.
    app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture
def as_logged_out():
    """
    Temporarily simulates no logged-in user at all - get_current_user
    returns None, exactly like a request with a missing or invalid token.
    """
    app.dependency_overrides[get_current_user] = lambda: None
    yield
    app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture(autouse=True)
def seed_and_cleanup():
    """Seeds 1 todo before each test and cleans the table after."""
    session = TestingSessionLocal()
    todo = Todos(
        id=1,
        title="Test Todo",
        description="This is a test todo",
        priority=3,
        complete=False,
        owner_id=1,
    )
    session.add(todo)
    session.commit()
    session.close()

    yield

    with engine.connect() as connection:
        connection.execute(text("DELETE FROM todos"))
        connection.commit()
