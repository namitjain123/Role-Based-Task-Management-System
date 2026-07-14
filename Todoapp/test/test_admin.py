from fastapi import status
from .conftest import *
from ..routers.admin import get_db, get_current_user
from ..models import Todos, Users
from fastapi .testclient import TestClient
client = TestClient(app)

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_admin_read_all_users(client, db):
    # seed a user so the listing has something to return
    user = Users(
        id=1, email="a@b.com", username="namit", first_name="Namit",
        last_name="Jain", hashed_password="hashed", is_active=True, role="admin",
    )
    db.add(user)
    db.commit()

    response = client.get("/api/admin/users")
    assert response.status_code == status.HTTP_200_OK

    body = response.json()
    assert len(body) == 1
    assert body[0]["username"] == "namit"
    # the password hash must never be exposed
    assert "hashed_password" not in body[0]

    db.query(Users).delete()
    db.commit()


def test_admin_read_single_user_not_found(client):
    response = client.get("/api/admin/users/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "User with the id 999 is not available"}


def test_admin_read_single_user_found(client, db):
    # the happy path was never actually covered before - only the 404 case was
    user = Users(
        id=5, email="found@b.com", username="findme", first_name="Find",
        last_name="Me", hashed_password="hashed", is_active=True, role="user",
    )
    db.add(user)
    db.commit()

    response = client.get("/api/admin/users/5")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["username"] == "findme"
    assert "hashed_password" not in body

    db.query(Users).delete()
    db.commit()


def test_admin_users_forbidden_for_non_admin(client, as_non_admin):
    # This is the actual RBAC enforcement test: proves a logged-in but
    # non-admin user is really rejected, not just assumed to be.
    response = client.get("/api/admin/users")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Admin access required"}


def test_admin_users_unauthorized_when_logged_out(client, as_logged_out):
    response = client.get("/api/admin/users")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Authentication required"}


def test_admin_read_all_authentication(client):
    response = client.get("/api/admin/todo/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{
        "complete": False, "title": "Test Todo",
        "description": "This is a test todo", "id": 1,
        "owner_id": 1, "priority": 3}]
    
def test_admin_delete_todo(client, db):
    response = client.delete("/api/admin/todo/1")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    todo = db.query(Todos).filter(Todos.id == 1).first()
    assert todo is None

def test_admin_delete_todo_not_found(client):
    response = client.delete("/api/admin/todo/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo with the id 999 is not available"}


def test_admin_todos_forbidden_for_non_admin(client, as_non_admin):
    response = client.get("/api/admin/todo/")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    # NOTE: this message differs from /admin/users' "Admin access required".
    # Same rule (must be admin), enforced by two different code paths -
    # this endpoint uses an inline check instead of the require_admin()
    # helper the /users routes use. Not a bug, but worth unifying later.
    assert response.json() == {"detail": "Access denied"}


def test_admin_delete_todo_forbidden_for_non_admin(client, as_non_admin, db):
    response = client.delete("/api/admin/todo/1")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # The real point of this test: a REJECTED request must have no side
    # effect. Checking only the status code wouldn't catch a bug where the
    # delete happened anyway before the check, or after a check that didn't
    # actually stop execution.
    todo = db.query(Todos).filter(Todos.id == 1).first()
    assert todo is not None