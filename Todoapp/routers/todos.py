from typing import Annotated
from fastapi import APIRouter, FastAPI, Depends, HTTPException, Path, Response, status,Request
from pydantic import BaseModel, Field

from Todoapp import models
from ..database import SessionLocal, engine
from Todoapp.models import Todos
from sqlalchemy.orm import Session
from Todoapp.routers import auth
from .auth import get_current_user
from starlette.responses import JSONResponse,RedirectResponse
from fastapi.templating import Jinja2Templates

template = Jinja2Templates(directory="Todoapp/templates")
router = APIRouter(
    prefix="/todos",
    tags=["todos"]
)

## create the database



def get_db():
    db = SessionLocal() # create a new database session
    try:
        yield db # yield the session to be used in the path operation
    finally:
        db.close()



db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[auth.Users, Depends(get_current_user)]

class TodoRequest(BaseModel):
    title: str =Field( min_length=3, max_length=50)
    description: str   =Field( min_length=3, max_length=200)
    priority: int   =Field(gt=0, lt=6)
    complete: bool  =Field(default=False)

def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie(key="access_token")
    return redirect_response



###Pages ###
#does three things:
#Checks if the user is logged in
#Fetches only that user’s todos
#Renders the todos HTML page
@router.get("/todos-page", status_code=status.HTTP_200_OK)
async def render_todos_page(
    request: Request,
    user: user_dependency,   # this will call get_current_user automatically
    db: db_dependency
):
    if user is None:
        return RedirectResponse("/auth/login-page", status_code=302)
    todos = db.query(models.Todos).filter(models.Todos.owner_id == user.id).all()
    return template.TemplateResponse(
        "todos.html",
        {"request": request, "todos": todos, "user": user}
    )

@router.get("/add-todo-page", status_code=status.HTTP_200_OK)
async def render_todo_page(
    request: Request,
    user: user_dependency
):
    return template.TemplateResponse(
        "add-todo.html",
        {"request": request, "user": user}
    )

@router.get("/edit-todo-page/{todo_id}", status_code=status.HTTP_200_OK)
async def render_edit_todo_page(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    todo_id: int = Path(gt=0)
):
    todo_model = (
        db.query(models.Todos)
        .filter(models.Todos.id == todo_id)
        .filter(models.Todos.owner_id == user.id)
        .first()
    )

    if todo_model is None:
        raise HTTPException(
            status_code=404,
            detail=f"Todo with the id {todo_id} is not available"
        )

    return template.TemplateResponse(
        "edit-todo.html",
        {"request": request, "todo": todo_model, "user": user}
    )










#####Endpoints ###
@router.get("/",status_code=status.HTTP_200_OK)
def read_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    return db.query(models.Todos).filter(models.Todos.owner_id == user.id).all()



@router.get("/todo/{todo_id}",status_code=status.HTTP_200_OK)
async def read_todo( user: user_dependency, db: db_dependency,todo_id:int =Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id)\
    .filter(models.Todos.owner_id == user.id).first()
    if todo_model is not None:
        return todo_model   
    raise HTTPException(status_code=404, detail=f"Todo with the id {todo_id} is not available")



@router.post("/todo/",status_code=status.HTTP_201_CREATED)
async def create_todo( user: user_dependency, db: db_dependency,todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    todo_model = models.Todos()
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete
    todo_model.owner_id = user.id
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)
    return todo_model
    
@router.put("/todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_todo( user: user_dependency, db: db_dependency,
                      todo_request: TodoRequest,
                      todo_id:int =Path(gt=0)):
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id)\
    .filter(models.Todos.owner_id == user.id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail=f"Todo with the id {todo_id} is not available")
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo( user: user_dependency, db: db_dependency,
                      todo_id:int =Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id)\
    .filter(models.Todos.owner_id == user.id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail=f"Todo with the id {todo_id} is not available")
    db.delete(todo_model)
    db.commit()
    return  