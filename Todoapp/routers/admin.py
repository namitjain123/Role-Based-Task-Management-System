from typing import Annotated
from fastapi import APIRouter, FastAPI, Depends, HTTPException, Path, Response, status
from pydantic import BaseModel, Field
from ..database import SessionLocal, engine
from ..models import Todos
from sqlalchemy.orm import Session
from Todoapp.routers import auth
from Todoapp import models
from .auth import get_current_user
router = APIRouter()

## create the database

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


    




