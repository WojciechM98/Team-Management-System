from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import datetime
from sqlalchemy.orm import Session

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
    class AssignedTasks(BaseModel):
        task_id: int = Field(..., description='ID of a task')
    
    class OwnedTasks(BaseModel):
        task_id: int = Field(..., description='ID of a task') 

    user_id: int = Field(..., description='ID of the user')
    owned_tasks: Optional[List[OwnedTasks]] = Field(None, description='Tasks owned by user')
    assigned_tasks: Optional[List[AssignedTasks]] = Field(None, description='Tasks assigned to user')

class UserCreate(UserBase):
    pass

class UserDelete(UserBase):
    user_id: int = Field(..., description='ID of the user')
    detail: str = Field(default='The user deletion operation has been performed successfully. '
                                'Tasks created by the user were deleted along with the user', 
                        description='Information about succesfull operation')

# Comment table models
class CommentBase(BaseModel):
    task_id: int = Field(..., description='ID of a parent task')
    timestamp: datetime.datetime = Field(..., description='Date and time when comment was added')
    comment: str = Field(..., description='Comment body')

class Comment(CommentBase):
    comment_id: int = Field(..., description='ID of a comment')


# Task table models
class TaskBase(BaseModel):

    class AssignedUsers(BaseModel):
        user_id: Optional[int] = Field(None, description='ID of a user')
        user_name: Optional[str] = Field(None, description='Name of a user')

    title: str = Field(...,min_length=5, max_length=512, description='Title of a task')
    owner_id: int = Field(..., description='ID of the user who created this task')
    start_date: Optional[datetime.date] = Field(None, description='Task start date. '
                                                'The default start date is the date task was created')
    end_date: Optional[datetime.date] = Field(None, description='Task end date')
    description: Optional[str] = Field(None, description='Description of a task')
    comments: Optional[List[Comment]] = Field(None, description='Task comments created by users')
    assigned_users: Optional[List[AssignedUsers]] = Field(None, description='Users assigned to the task')
    
class Task(TaskBase):
    task_id: int = Field(..., description='ID of a task')

class TaskAdd(TaskBase):
    pass

class TaskDelete(Task):
    detail: str = Field(default='The task deletion operation has been performed successfully', 
                      description='Information about succesfull operation')





app = FastAPI()

@app.get('/users', response_model=List[User])
def get_users(instance: Session = Depends(db.get_session)):
    """Return all items from Users table"""
    users = instance.query(db.UserT).all()
    return users

@app.get('/users/{user_id}', response_model=User)
def get_user(user_id: int, instance: Session = Depends(db.get_session)):
    """Find user by passing user_id"""
    user = instance.query(db.UserT).filter(db.UserT.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail='User not found. Operation rejected.')
    return user

@app.post('/users/add', response_model=User)
def create_user(user: UserCreate, instance: Session = Depends(db.get_session)):
    """Create new user db.UserT class by passing UserCreate variables"""
    new_user = db.UserT(user_name=user.user_name)
    instance.add(new_user)
    instance.commit()
    instance.refresh(new_user)
    return new_user

@app.delete('/users/delete/{user_id}', response_model=UserDelete)
def delete_user(user_id: int, instance: Session = Depends(db.get_session)):
    """Delete user by entering his ID and tasks that he owns"""
    user_to_del = instance.query(db.UserT).filter(db.UserT.user_id == user_id)
    result = user_to_del.first()
    if result is not None:
        user_to_del.delete()
        instance.commit()
    else:
        raise HTTPException(status_code=404, detail='User not found. Operation rejected.')
    return result


# API task endpoints

@app.get('/tasks', response_model=List[Task])
def get_tasks(instance: Session = Depends(db.get_session)):
    """Return all tasks"""
    tasks = instance.query(db.TaskT).all()
    print(tasks)
    return tasks

@app.get('/tasks/{task_id}', response_model=Task)
def get_task(task_id: int, instance: Session = Depends(db.get_session)):
    """Return one task by entering task ID"""
    task = instance.query(db.TaskT).filter(db.TaskT.task_id == task_id)
    result = task.first()
    # print(f'\n\nTask: {task}\n\n')
    # print(f'\n\nresult: {result }\n\n')
    if result is None:
        raise HTTPException(status_code=404, detail='Task not found. Operation rejected.')
    return result

@app.post('/tasks/add', response_model=Task)
def add_task(user_id: int, title: str, description: str = None, instance: Session = Depends(db.get_session)):
    """Add new task"""
    new_task = db.TaskT(user_id, title, description)
    instance.add(new_task)
    instance.commit()
    instance.refresh(new_task)
    return new_task

@app.delete('/tasks/delete/{task_id}', response_model=TaskDelete)
def delete_task(task_id: int, instance: Session = Depends(db.get_session)):
    """Delete task"""
    task_to_del = instance.query(db.TaskT).filter(db.TaskT.task_id == task_id)
    result = task_to_del.first()
    if result is not None:
        task_to_del.delete()
        instance.commit()
    else:
        raise HTTPException(status_code=404, detail='User not found. Operation rejected.')
    return result

@app.post('/task/addcomment', response_model=Comment)
def comment_task(user_id: int, task_id: int, comment: str, instance: Session = Depends(db.get_session)):
    user = instance.execute(db.select(db.UserT).where(db.UserT.user_id == user_id)).scalar()
    # Checking if user exist
    if user is None:
        raise HTTPException(status_code=404, detail='User not found. Operation rejected.')
    task = instance.execute(db.select(db.TaskT).where(db.TaskT.task_id == task_id)).scalar()
    # Checking if task exist
    if task is None:
        raise HTTPException(status_code=404, detail='Task not found. Operation rejected.')
    # Checking if user owns or is assigned to task - only if user can comment
    is_assigned = [t.task_id for t in user.assigned_tasks if t.task_id == task.task_id]
    is_owned = [t.task_id for t in user.owned_tasks if t.task_id == task.task_id]
    if not (is_owned or is_assigned):
        raise HTTPException(status_code=403, detail='Permission denied. This user does not have permission to comment this task')
    # Creating new comment, appending it to relationships list in task.comments finally commit
    new_comment = db.CommentT(task_id, comment)
    task.comments.append(new_comment)
    instance.add(task)
    instance.commit()
    return new_comment

   