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

    response = client.get("/admin/users")
    assert response.status_code == status.HTTP_200_OK

    body = response.json()
    assert len(body) == 1
    assert body[0]["username"] == "namit"
    # the password hash must never be exposed
    assert "hashed_password" not in body[0]

    db.query(Users).delete()
    db.commit()


def test_admin_read_single_user_not_found(client):
    response = client.get("/admin/users/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "User with the id 999 is not available"}


def test_admin_read_all_authentication(client):
    response = client.get("/admin/todo/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{
        "complete": False, "title": "Test Todo",
        "description": "This is a test todo", "id": 1,
        "owner_id": 1, "priority": 3}]
    
def test_admin_delete_todo(client, db):
    response = client.delete("/admin/todo/1")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    todo = db.query(Todos).filter(Todos.id == 1).first()
    assert todo is None

def test_admin_delete_todo_not_found(client):
    response = client.delete("/admin/todo/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo with the id 999 is not available"}