"""Pytest fixtures for the API."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from pisec_server.auth.dependencies import get_current_user
from pisec_server.db.database import GeneralDBConnector, get_db
from pisec_server.db.db_models import Base, Camera, CameraCredential, User
from pisec_server.main import app

"""Setup for the test database."""


def _seed_test_db() -> None:
    """Add data to the database."""
    test_users: list[User] = [
        User(id=1, email="user1@test.com", password_hash="password1", is_admin=True),
        User(id=2, email="user2@test.com", password_hash="password2"),
    ]
    test_credentials: list[CameraCredential] = [
        CameraCredential(client_id="1:1", user_id=1, camera_id=1, client_secret_hash="1234"),
        CameraCredential(client_id="1:2", user_id=1, camera_id=2, client_secret_hash="5678"),
        CameraCredential(client_id="1:3", user_id=2, camera_id=3, client_secret_hash="secret"),
    ]
    test_cameras: list[Camera] = [
        Camera(
            id=1,
            name="camera-1",
            mac_address="A1:B2:C3:D4:E5:F6",
        ),
        Camera(
            id=2,
            name="camera-2",
            mac_address="F6:E5:D4:C3:B2:A1",
        ),
        Camera(
            id=3,
            name="camera-3",
            mac_address="A6:B5:C4:D3:E2:F1",
        ),
    ]

    db = db_connector.get_session()
    try:
        # Add test users
        if db.query(User).count() == 0:
            db.add_all(test_users)
        # Add test credentials
        if db.query(CameraCredential).count() == 0:
            db.add_all(test_credentials)
        # Add test cameras
        if db.query(Camera).count() == 0:
            db.add_all(test_cameras)

        db.commit()
    finally:
        db.close()


# Create the test database connector
db_connector = GeneralDBConnector(
    database_url="sqlite://",
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    poolclass=__import__("sqlalchemy.pool").pool.StaticPool,  # pyright: ignore[reportAny]
)


"""FastAPI dependency overrides."""


def get_test_db() -> Generator[Session]:
    """Returns a test instance of the database that you can query against. This overrides a dependency."""
    db: Session = db_connector.get_session()
    try:
        yield db
    finally:
        db.close()


def get_current_test_user() -> User:
    """Returns the 'logged in' user from the test database. This overrides a dependency."""
    user: User | None = db_connector.get_session().query(User).filter(User.email == "user1@test.com").first()
    assert user is not None  # If test db was set up correctly, this should always be true
    return user


def get_current_test_admin_user() -> User:
    """Returns the 'logged in' test user that is an admin. This overrides a dependency."""
    user: User = get_current_test_user()
    assert user.is_admin
    return user


"""Pytest fixtures"""


@pytest.fixture()
def client() -> Generator[TestClient]:
    """Fixture for getting a fastapi test client."""
    # Reset the database contents
    Base.metadata.drop_all(bind=db_connector.get_engine())
    Base.metadata.create_all(bind=db_connector.get_engine())
    _seed_test_db()

    # Override the dependencies used in the fastapi project
    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[get_current_user] = get_current_test_user

    with TestClient(app) as test_client:
        yield test_client

    # Undo the overrides
    app.dependency_overrides.clear()
