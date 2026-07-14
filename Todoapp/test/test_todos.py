from fastapi import status
from Todoapp.models import Todos

def test_read_all_authenticated(client):
    response = client.get("/api/todos/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{
        "complete": False,
        "description": "This is a test todo",
        "id": 1,
        "owner_id": 1,
        "priority": 3,
        "title": "Test Todo",
    }]

def test_read_one_authenticated(client):
    response = client.get("/api/todos/todo/1")
    assert response.status_code == status.HTTP_200_OK

def test_read_one_not_found(client):
    response = client.get("/api/todos/todo/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_create_todo_authenticated(client, db):
    response = client.post("/api/todos/todo/", json={
        "title": "New Todo",
        "description": "This is a new todo",
        "priority": 2,
        "complete": False
    })
    assert response.status_code == status.HTTP_201_CREATED

    todo = db.query(Todos).filter(Todos.id == 2).first()
    assert todo is not None
    assert todo.title == "New Todo"

def test_update_todo_authenticated(client, db):
    response = client.put("/api/todos/todo/1", json={
        "title": "Updated Todo",
        "description": "This is an updated todo",
        "priority": 1,
        "complete": True
    })
    assert response.status_code == status.HTTP_204_NO_CONTENT

    todo = db.query(Todos).filter(Todos.id == 1).first()
    assert todo.title == "Updated Todo"

def test_delete_todo_authenticated(client, db):
    response = client.delete("/api/todos/todo/1")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    todo = db.query(Todos).filter(Todos.id == 1).first()
    assert todo is None
