from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, Path, status,Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware


from .database import SessionLocal, engine
from .models import Base
from fastapi.staticfiles import StaticFiles

from .routers import auth,todos,admin, users

from fastapi.responses import RedirectResponse

app = FastAPI()

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
