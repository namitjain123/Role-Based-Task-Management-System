import os
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, Path, status,Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware


from .database import SessionLocal, engine
from .models import Base
from fastapi.staticfiles import StaticFiles

from .routers import auth,todos,admin, users

from fastapi.responses import RedirectResponse

app = FastAPI()

# Allow the React dev server (and, later, your deployed frontend) to call this API
# from the browser. Without this, the browser blocks cross-origin requests.
# FRONTEND_ORIGINS can be overridden by an env var in production (comma-separated).
frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

## create the database
Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="Todoapp/static"), name="static")    

@app.get("/", status_code=status.HTTP_200_OK)
def test(request: Request):
    return RedirectResponse(url="/todos/todos-page", status_code=status.HTTP_302_FOUND)

@app.get("/healthy")
def healthy():
    return {"status": "healthy"}

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)
