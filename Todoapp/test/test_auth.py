"""
Tests for registration, login and the REAL JWT check.

Every other test file fakes the logged-in user, so get_current_user's token
handling is never exercised there. This file is where it actually gets tested.
"""
import asyncio
from datetime import timedelta

import pytest
from fastapi import HTTPException, status
from jose import jwt

from Todoapp.models import Users
from Todoapp.routers.auth import (
    ALGORITHM,
    SECRET_KEY,
    bcrypt_context,
    create_access_token,
    get_current_user,
)

NEW_USER = {
    "email": "alice@example.com",
    "username": "alice",
    "first_name": "Alice",
    "last_name": "Smith",
    "password": "Secret123!",
    "role": "user",
}


@pytest.fixture
def alice(db):
    """A real user saved in the test DB with a bcrypt-hashed password."""
    user = Users(
        id=1, email="alice@example.com", username="alice", first_name="Alice",
        last_name="Smith", hashed_password=bcrypt_context.hash("Secret123!"),
        is_active=True, role="user",
    )
    db.add(user)
    db.commit()
    return user


def login(client, username, password):
    # /auth/token is an OAuth2 form endpoint, so it takes form data, not JSON
    return client.post("/api/auth/token", data={"username": username, "password": password})


# ---------------------------------------------------------------- register

def test_register_creates_user_with_hashed_password(client, db):
    response = client.post("/api/auth/", json=NEW_USER)
    assert response.status_code == status.HTTP_201_CREATED

    user = db.query(Users).filter(Users.username == "alice").first()
    assert user is not None
    assert user.email == "alice@example.com"
    assert user.role == "user"
    assert user.is_active is True
    # The plain password must never be stored, but it must still verify.
    assert user.hashed_password != "Secret123!"
    assert bcrypt_context.verify("Secret123!", user.hashed_password)


def test_register_missing_field_is_rejected(client, db):
    incomplete = {k: v for k, v in NEW_USER.items() if k != "password"}
    response = client.post("/api/auth/", json=incomplete)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert db.query(Users).count() == 0


# ------------------------------------------------------------------- login

def test_login_returns_valid_jwt(client, alice):
    response = login(client, "alice", "Secret123!")
    assert response.status_code == status.HTTP_200_OK

    body = response.json()
    assert body["token_type"] == "bearer"

    claims = jwt.decode(body["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
    assert claims["sub"] == "alice"
    assert claims["user_id"] == 1
    assert claims["role"] == "user"
    assert "exp" in claims  # tokens must expire


def test_login_wrong_password(client, alice):
    response = login(client, "alice", "wrong-password")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Invalid username or password"}


def test_login_unknown_user(client):
    response = login(client, "nobody", "whatever")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # Same message as a wrong password, so attackers can't tell which
    # usernames exist.
    assert response.json() == {"detail": "Invalid username or password"}


# ----------------------------------------------- get_current_user (real JWT)

def test_get_current_user_with_valid_token(db, alice):
    token = create_access_token("alice", 1, "user")
    user = asyncio.run(get_current_user(token=token, db=db))
    assert user.username == "alice"


def test_get_current_user_without_token_returns_none(db):
    assert asyncio.run(get_current_user(token=None, db=db)) is None


def test_get_current_user_rejects_tampered_token(db, alice):
    forged = jwt.encode({"sub": "alice", "user_id": 1, "role": "admin"},
                        "not-the-real-secret", algorithm=ALGORITHM)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user(token=forged, db=db))
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_rejects_expired_token(db, alice):
    expired = create_access_token("alice", 1, "user", expires_delta=timedelta(minutes=-1))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user(token=expired, db=db))
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_rejects_token_missing_claims(db):
    token = jwt.encode({"sub": "alice"}, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user(token=token, db=db))
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------- full flow over HTTP, no fake user

def test_login_then_use_token_on_protected_route(client, alice, real_auth):
    token = login(client, "alice", "Secret123!").json()["access_token"]

    response = client.get("/api/todos/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    # The seeded todo belongs to user id 1, which is alice.
    assert [t["title"] for t in response.json()] == ["Test Todo"]


def test_protected_route_rejects_garbage_token(client, real_auth):
    response = client.get("/api/todos/", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_regular_user_token_cannot_reach_admin_route(client, alice, real_auth):
    # RBAC with a REAL token: the role comes from the database user, not a fake.
    token = login(client, "alice", "Secret123!").json()["access_token"]
    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_403_FORBIDDEN
