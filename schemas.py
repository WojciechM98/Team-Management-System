from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, model_serializer
from typing import Optional, List
import datetime
from sqlalchemy.orm import Session
import db
from pwhshr import Password, PasswordHash

# User table models
class UserBase(BaseModel):
    """Base User model"""
    username: str = Field(..., min_length=3, max_length=512, description='Name of a user')
    email: Optional[str] = Field(None, description='User email adress')

class UserWithID(UserBase):
    user_id: int = Field(..., description='ID of the user')
    
class User(UserWithID):
    class AssignedTasks(BaseModel):
        task_id: int = Field(..., description='ID of a task')
    
    class OwnedTasks(BaseModel):
        task_id: int = Field(..., description='ID of a task') 

    owned_tasks: Optional[List[OwnedTasks]] = Field(None, description='Tasks owned by user')
    assigned_tasks: Optional[List[AssignedTasks]] = Field(None, description='Tasks assigned to user')


class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=512, description='Name of a user')
    email: Optional[str] = Field(None, description='User email adress')
    

class UserDelete(UserBase):
    user_id: int = Field(..., description='ID of the user')
    detail: str = Field(default='The user deletion operation has been performed successfully. '
                                'Tasks created by the user were deleted along with the user', 
                        description='Information about succesfull operation')


# Task table models

class TaskBase(BaseModel):
    title: str = Field(...,min_length=5, max_length=512, description='Title of a task')
    description: Optional[str] = Field(None, description='Description of a task')
    
class Task(TaskBase):
    task_id: int = Field(..., description='ID of a task')
    owner_id: int = Field(..., description='ID of the user who created this task')
    start_date: Optional[datetime.date] = Field(None, description='Task start date. '
                                                'The default start date is the date task was created')
    end_date: Optional[datetime.date] = Field(None, description='Task end date')
    comments: Optional[List['Comment']] = Field(None, description='Task comments created by users')
    assigned_users: Optional[List['UserWithID']] = Field(None, description='Users assigned to the task')

class TaskAdd(TaskBase):
    pass

class TaskAssign(BaseModel):
    user_id: int = Field(..., description='ID of a assigned user')

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=512, description='Title of a task')
    description: Optional[str] = Field(None, description='Description of a task')
    
    start_date: Optional[datetime.date] = Field(None, description='Task start date. '
                                                'The default start date is the date task was created')
    end_date: Optional[datetime.date] = Field(None, description='Task end date')
    #assigned_users: Optional[List['User']] = Field(None, description='Users assigned to the task')

class TaskDelete(Task):
    detail: str = Field(default='The task deletion operation has been performed successfully. '
                                'The task comments were deleted along with the task.', 
                      description='Information about succesfull operation')

# Comment table models

class CommentBase(BaseModel):
    # task_id: int = Field(..., description='ID of a parent task') # No need to show this info 
    user_id: int = Field(..., description='ID of a user')
    timestamp: datetime.datetime = Field(..., description='Date and time when comment was added')
    comment: str = Field(..., description='Comment body')

class Comment(CommentBase):
    comment_id: int = Field(..., description='ID of a comment')

class CommentUpdate(BaseModel):
    timestamp: Optional[datetime.datetime] = Field(None, description='Date and time when comment was added')
    comment: Optional[str] = Field(None, description='Comment body')

class CommentDelete(Comment):
    detail: str = Field(default='Comment deletion operation has been performed successfully.',
                        description='Information about succesfull operation')

