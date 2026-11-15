"""Tests for routers/users.py: profile lookup and password change."""
from types import SimpleNamespace

import pytest
from fastapi import status

from Todoapp.main import app
from Todoapp.models import Users
from Todoapp.routers.auth import bcrypt_context, get_current_user

from .conftest import override_get_current_user

PASSWORD_URL = "/api/user/user/password"  # router prefix /user + route /user/password


@pytest.fixture
def stored_user(db):
    """
    Saves a real user and makes the fake login return it, including
    hashed_password, which change_password needs to verify the old password.
    """
    hashed = bcrypt_context.hash("OldPass123!")
    db.add(Users(id=1, email="n@example.com", username="namit", first_name="Namit",
                 last_name="Jain", hashed_password=hashed, is_active=True, role="admin"))
    db.commit()

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="namit", role="admin", hashed_password=hashed
    )
    yield
    app.dependency_overrides[get_current_user] = override_get_current_user


def current_hash(db):
    db.expire_all()  # re-read from the DB instead of the session's cached copy
    return db.query(Users).filter(Users.id == 1).first().hashed_password


# ------------------------------------------------------------- GET /user/

def test_get_user_as_admin_returns_own_profile(client, stored_user):
    response = client.get("/api/user/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "namit"


def test_get_user_forbidden_for_non_admin(client, as_non_admin):
    response = client.get("/api/user/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_user_logged_out(client, as_logged_out):
    response = client.get("/api/user/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------- PUT /user/password

def test_change_password_success(client, db, stored_user):
    response = client.put(PASSWORD_URL, json={"password": "OldPass123!",
                                              "new_password": "NewPass456!"})
    assert response.status_code == status.HTTP_204_NO_CONTENT

    new_hash = current_hash(db)
    assert bcrypt_context.verify("NewPass456!", new_hash)
    assert not bcrypt_context.verify("OldPass123!", new_hash)


def test_change_password_wrong_current_password(client, db, stored_user):
    before = current_hash(db)
    response = client.put(PASSWORD_URL, json={"password": "WrongPass!",
                                              "new_password": "NewPass456!"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert current_hash(db) == before  # nothing changed


def test_change_password_same_as_old_rejected(client, db, stored_user):
    before = current_hash(db)
    response = client.put(PASSWORD_URL, json={"password": "OldPass123!",
                                              "new_password": "OldPass123!"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert current_hash(db) == before


def test_change_password_logged_out(client, as_logged_out):
    response = client.put(PASSWORD_URL, json={"password": "a", "new_password": "b"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
