from typing import Annotated
from fastapi import APIRouter, FastAPI, Depends, HTTPException, Path, Response, status, Request
from pydantic import BaseModel, Field
from ..database import SessionLocal, engine
from ..models import Todos
from sqlalchemy.orm import Session
from Todoapp.routers import auth
from Todoapp import models
from .auth import get_current_user
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
router = APIRouter()

## create the database

template = Jinja2Templates(directory="Todoapp/templates")
router= APIRouter(
    prefix="/admin",
    tags=["admin"]
)

def get_db():
    db = SessionLocal() # create a new database session
    try:
        yield db # yield the session to be used in the path operation
    finally:
        db.close()



db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[auth.Users, Depends(get_current_user)]


# Shape of a user we send back to an admin.
# It deliberately leaves out hashed_password so the hash is never exposed.
class UserResponse(BaseModel):
    id: int
    email: str | None = None
    username: str
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool
    role: str

    class Config:
        from_attributes = True  # lets FastAPI build this straight from the ORM object


def require_admin(user):
    """Raise if the caller is missing or not an admin. Used by every admin route."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")





@router.get("/users-page", status_code=status.HTTP_200_OK)
async def render_users_page(request: Request, user: user_dependency, db: db_dependency):
    """HTML page (cookie auth): shows a table of all users to an admin."""
    if user is None:
        return RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    if user.role != "admin":
        # a logged-in non-admin gets sent back to their own todos
        return RedirectResponse(url="/todos/todos-page", status_code=status.HTTP_302_FOUND)
    users = db.query(models.Users).all()
    return template.TemplateResponse(
        "admin-users.html",
        {"request": request, "users": users, "user": user},
    )


@router.get("/users", status_code=status.HTTP_200_OK, response_model=list[UserResponse])
def read_all_users(user: user_dependency, db: db_dependency):
    """Admin only: list every registered user (without password hashes)."""
    require_admin(user)
    return db.query(models.Users).all()


@router.get("/users/{user_id}", status_code=status.HTTP_200_OK, response_model=UserResponse)
def read_user(user: user_dependency, db: db_dependency, user_id: int = Path(gt=0)):
    """Admin only: fetch a single user by id."""
    require_admin(user)
    user_model = db.query(models.Users).filter(models.Users.id == user_id).first()
    if user_model is None:
        raise HTTPException(status_code=404, detail=f"User with the id {user_id} is not available")
    return user_model


@router.get("/todo/",status_code=status.HTTP_200_OK)
def read_all_todos(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return db.query(models.Todos).all()

@router.delete("/todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo( user: user_dependency, db: db_dependency,
                      todo_id:int =Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail=f"Todo with the id {todo_id} is not available")
    db.delete(todo_model)
    db.commit()


    




