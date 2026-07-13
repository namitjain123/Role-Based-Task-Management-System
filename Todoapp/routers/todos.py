import os
import json
from typing import Annotated
from fastapi import APIRouter, FastAPI, Depends, HTTPException, Path, Response, status,Request
from pydantic import BaseModel, Field
import httpx

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

class ParseTodoRequest(BaseModel):
    text: str = Field(min_length=3, max_length=500, example="email the design team about the Q3 report by friday, high priority")

class ParsedTodo(BaseModel):
    title: str
    description: str
    priority: int

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

PARSE_SYSTEM_PROMPT = """You are a task-parsing assistant for a todo app.
Given a short piece of natural language, extract a structured todo.

Respond with ONLY a JSON object, no other text, in exactly this shape:
{"title": "...", "description": "...", "priority": <integer 1-5>}

Rules:
- title: concise summary, 3 to 50 characters.
- description: 3 to 200 characters. Restate the task with any extra detail
  the input gives (who, what, when). If there's nothing beyond the title,
  just restate the title as a full sentence.
- priority: integer 1 (lowest) to 5 (highest). Infer urgency from words like
  "urgent", "asap", "whenever", "no rush", explicit deadlines, etc.
  Default to 3 if nothing suggests otherwise.
"""

def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie(key="access_token")
    return redirect_response



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



@router.post("/parse", status_code=status.HTTP_200_OK, response_model=ParsedTodo)
async def parse_todo_text(user: user_dependency, request: ParseTodoRequest):
    """
    Turns a natural-language sentence into structured todo fields via Groq's
    LLM API. Does NOT create a todo - it only returns suggested field values
    so the user can review/edit them before actually submitting via the
    normal POST /todos/todo/ endpoint above.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="AI parsing is not configured on the server (missing GROQ_API_KEY).",
        )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": PARSE_SYSTEM_PROMPT},
                        {"role": "user", "content": request.text},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2,
                },
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach the AI service: {exc}")

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"AI service error ({response.status_code}): {response.text[:200]}",
        )

    try:
        completion = response.json()
        raw_content = completion["choices"][0]["message"]["content"]
        parsed = json.loads(raw_content)

        title = str(parsed.get("title", "")).strip()[:50]
        description = str(parsed.get("description", "")).strip()[:200]
        priority = int(parsed.get("priority", 3))
        priority = max(1, min(5, priority))  # clamp into the 1-5 range TodoRequest requires

        # Fall back to the user's raw text if the model returned something
        # too short to pass TodoRequest's own min_length=3 validation later.
        if len(title) < 3:
            title = (request.text.strip()[:50] or "Untitled")
        if len(description) < 3:
            description = request.text.strip()[:200]

    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not understand the AI's response: {exc}",
        )

    return ParsedTodo(title=title, description=description, priority=priority)


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