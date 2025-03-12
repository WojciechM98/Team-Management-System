from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

import db
from enum import IntEnum

class Priority(IntEnum):
    """Priority can be used later for task management"""
    LOW = 3
    MEDIUM = 2
    HIGH = 1

# User table models
class UserBase(BaseModel):
    """Base schematic for User model"""
    # TODO: How to set max_length with SQLAlchemy.String which is set to String(512)?
    user_name: str = Field(..., min_length=3, max_length=512, description='Name of a user')
    
class User(UserBase):
    user_id: int = Field(..., description='ID of the user')
    owned_tasks: Optional[int] = Field(..., description='Tasks owned by user')
    assigned_tasks: Optional[int] = Field(..., description='Tasks assigned to user')

class UserCreate(UserBase):
    pass

class UserDelete(User):
    user_id: int = Field(..., description='ID of the user')
    detail: str = Field(default='The deletion operation has been performed successfully', 
                      description='Information about succesfull operation')

# Task table models
class TaskBase(BaseModel):
    class Config:
        arbitrary_types_allowed=True

    title: str = Field(...,min_length=5, max_length=512, description='Title of a task')
    created_by_user_id: int = Field(..., description='ID of the user who created this task')
    start_date: datetime.date = Field(..., description='Task start date')
    end_date: Optional[datetime.date] = Field(..., description='Task end date')
    description: Optional[str] = Field(..., description='Description of a task')
    class AssignedUsers(BaseModel):
        user_id: int = Field(..., description='ID of a user')
        user_name: str = Field(..., description='Name of a user')
    assigned_users: Optional[AssignedUsers] = Field(..., description='Users assigned to the task')
    

app = FastAPI()

@app.get('/users', response_model=List[User])
def get_users():
    """Return all items from Users table"""
    users = db.session.query(db.UserT).all()
    return users

@app.get('/users/{user_id}', response_model=User)
def get_user(user_id: int):
    """Find user by passing user_id"""
    user = db.session.query(db.UserT).filter(db.UserT.user_id == user_id).first()
    return user

@app.post('/users/add', response_model=User)
def create_user(user: UserCreate):
    """Create new user db.UserT class by passing UserCreate variables"""
    new_user = db.UserT(user_name=user.user_name)
    db.session.add(new_user)
    db.session.commit()
    db.session.refresh(new_user)
    return new_user

@app.delete('/users/delete/{user_id}', response_model=UserDelete)
def delete_user(user_id: int):
    """Delete user by entering his ID"""
    user_to_del = db.session.query(db.UserT).filter(db.UserT.user_id == user_id)
    result = user_to_del.first()
    if result is not None:
        user_to_del.delete()
        db.session.commit()
    else:
        raise HTTPException(status_code=404, detail="User not found. Operation rejected.")
    return result


# API task endpoints

@app.get('/tasks', response_model=List[TaskBase])
def get_tasks():
    """Return all tasks"""
    tasks = db.session.query(db.TaskT).all()
    return tasks