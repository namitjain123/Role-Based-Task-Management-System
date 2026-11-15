import pytest
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


# ---------------------------------------------------------------------------
# Ownership: a user must never see or change someone else's todos.
# The seeded todo (id=1) belongs to user 1; as_non_admin logs in as user 2.
# The API answers 404 (not 403) so it doesn't reveal that the todo exists.
# ---------------------------------------------------------------------------

def test_other_user_sees_empty_list(client, as_non_admin):
    response = client.get("/api/todos/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_other_user_cannot_read_todo(client, as_non_admin):
    response = client.get("/api/todos/todo/1")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_other_user_cannot_update_todo(client, db, as_non_admin):
    response = client.put("/api/todos/todo/1", json={
        "title": "Hacked", "description": "Not my todo", "priority": 1, "complete": True,
    })
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert db.query(Todos).filter(Todos.id == 1).first().title == "Test Todo"


def test_other_user_cannot_delete_todo(client, db, as_non_admin):
    response = client.delete("/api/todos/todo/1")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert db.query(Todos).filter(Todos.id == 1).first() is not None


def test_created_todo_belongs_to_creator(client, db, as_non_admin):
    client.post("/api/todos/todo/", json={
        "title": "Bob's todo", "description": "Mine", "priority": 2, "complete": False,
    })
    todo = db.query(Todos).filter(Todos.title == "Bob's todo").first()
    assert todo.owner_id == 2


# ---------------------------------------------------------------------------
# Logged out. These routes return 400 "Invalid user" today; 401 would be the
# more standard status code, but the tests document current behaviour.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method, url", [
    ("get", "/api/todos/"),
    ("get", "/api/todos/todo/1"),
    ("delete", "/api/todos/todo/1"),
])
def test_logged_out_is_rejected(client, as_logged_out, method, url):
    response = getattr(client, method)(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_logged_out_cannot_create(client, db, as_logged_out):
    response = client.post("/api/todos/todo/", json={
        "title": "Ghost", "description": "No owner", "priority": 2, "complete": False,
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert db.query(Todos).count() == 1  # only the seeded todo


def test_logged_out_cannot_update(client, db, as_logged_out):
    response = client.put("/api/todos/todo/1", json={
        "title": "Ghost edit", "description": "No owner", "priority": 2, "complete": False,
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert db.query(Todos).filter(Todos.id == 1).first().title == "Test Todo"


# ---------------------------------------------------------------------------
# Validation: TodoRequest says title 3-50 chars, description 3-200,
# priority 1-5. Bad input must get 422 and must not be saved.
# ---------------------------------------------------------------------------

VALID_TODO = {"title": "Valid title", "description": "Valid description",
              "priority": 3, "complete": False}


@pytest.mark.parametrize("field, bad_value", [
    ("title", "ab"),               # too short
    ("title", "x" * 51),           # too long
    ("description", "ab"),         # too short
    ("description", "x" * 201),    # too long
    ("priority", 0),               # below range
    ("priority", 6),               # above range
    ("priority", "high"),          # wrong type
])
def test_create_todo_invalid_input(client, db, field, bad_value):
    response = client.post("/api/todos/todo/", json={**VALID_TODO, field: bad_value})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert db.query(Todos).count() == 1  # nothing new saved


@pytest.mark.parametrize("missing", ["title", "description", "priority"])
def test_create_todo_missing_field(client, missing):
    body = {k: v for k, v in VALID_TODO.items() if k != missing}
    response = client.post("/api/todos/todo/", json=body)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_todo_invalid_input_leaves_todo_unchanged(client, db):
    response = client.put("/api/todos/todo/1", json={**VALID_TODO, "priority": 10})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert db.query(Todos).filter(Todos.id == 1).first().priority == 3


def test_todo_id_must_be_positive(client):
    response = client.get("/api/todos/todo/0")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_missing_todo_returns_404(client):
    response = client.put("/api/todos/todo/999", json=VALID_TODO)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_missing_todo_returns_404(client):
    response = client.delete("/api/todos/todo/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
