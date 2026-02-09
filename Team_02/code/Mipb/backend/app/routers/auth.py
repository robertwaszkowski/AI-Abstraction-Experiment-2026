
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from pydantic import BaseModel
from typing import List

router = APIRouter()

class UserSchema(BaseModel):
    id: int
    username: str
    full_name: str
    role_name: str

@router.get("/users", response_model=List[UserSchema])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
