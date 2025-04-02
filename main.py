from fastapi import FastAPI, HTTPException, Depends, APIRouter
from pydantic import BaseModel, Field, model_serializer
from typing import Optional, List, Annotated
import datetime
from sqlalchemy.orm import Session
import db
from pwhshr import Password, PasswordHash
from schemas import *
import security as sc

app = FastAPI()
auth = APIRouter(dependencies=[Depends(sc.get_current_user)])

@app.post('/token')
async def login_for_access_token(form_data: Annotated[sc.OAuth2PasswordRequestForm, Depends()],
                                 instance: Session = Depends(db.get_session)) -> sc.Token:
    result = sc.login_for_access_token_function(form_data, instance)
    return result

@auth.get('/users/me', response_model=User)
async def get_me(current_user: Annotated[User, Depends(sc.get_current_user)]):
    return current_user

@auth.get('/users', response_model=List[User])
def get_users(instance: Session = Depends(db.get_session)):
    """Return all items from Users table"""
    users = instance.execute(db.select(db.UserT)).unique().scalars()
    result = [user for user in users]
    return result

@auth.get('/users/{user_id}', response_model=User)
def get_user(user_id: int, instance: Session = Depends(db.get_session)):
    """Find user by passing user_id"""
    user = instance.execute(db.select(db.UserT).where(db.UserT.user_id == user_id)).scalar()
    if user is None:
        raise HTTPException(status_code=404, detail='User not found. Operation rejected.')
    return user

@auth.post('/users/add', response_model=User)
def create_user(username: str, email: str, password: str, instance: Session = Depends(db.get_session)):
    """Create new user db.UserT class by passing UserCreate variables"""
    new_user = db.UserT(username, email, password)
    instance.add(new_user)
    instance.commit()
    instance.refresh(new_user)
    return new_user

@auth.post('/users/update', response_model=User)
def update_user(user_id: int, params: UserUpdate, instance: Session = Depends(db.get_session)):
    """Update user"""
    user_to_update = instance.execute(db.select(db.UserT).where(db.UserT.user_id == user_id)).scalar()
    # Updating user information with model_dump() and setattr()
    update_data = params.model_dump(exclude_unset=True)
    [setattr(user_to_update, key, value) for key, value in update_data.items()]
    instance.commit()
    return user_to_update

@auth.delete('/users/delete/{user_id}', response_model=UserDelete)
def delete_user(user_id: int, instance: Session = Depends(db.get_session)):
    """Delete user by entering his ID and tasks that he owns"""
    user_to_del = instance.execute(db.select(db.UserT).where(db.UserT.user_id == user_id)).scalar()
    if user_to_del is not None:
        instance.delete(user_to_del)
        instance.commit()
    else:
        raise HTTPException(status_code=404, detail='User not found. Operation rejected.')
    return user_to_del


# API task endpoints

@auth.get('/tasks', response_model=List[Task])
def get_tasks(instance: Session = Depends(db.get_session)):
    """Return all tasks"""
    tasks = instance.execute(db.select(db.TaskT)).unique().scalars()
    # Task list comprehension
    result = [task for task in tasks]
    return result

@auth.get('/tasks/{task_id}', response_model=Task)
def get_task(task_id: int, instance: Session = Depends(db.get_session)):
    """Return one task by entering task ID"""
    task = instance.execute(db.select(db.TaskT).where(db.TaskT.task_id == task_id)).scalar()
    if task is None:
        raise HTTPException(status_code=404, detail='Task not found. Operation rejected.')
    return task

@auth.post('/tasks/add', response_model=Task)
def add_task(user_id: int, title: str, description: str, instance: Session = Depends(db.get_session)):
    """Add new task"""
    new_task = db.TaskT(user_id, title, description)
    instance.add(new_task)
    instance.commit()
    return new_task

@auth.post('/tasks/update', response_model=Task)
def update_task(user_id: int, task_id: int, params: TaskUpdate, instance: Session = Depends(db.get_session)):
    """Update task"""
    user = instance.execute(db.select(db.UserT).where(db.UserT.user_id == user_id)).scalar()
    if user is None: # Check is user exist
        raise HTTPException(status_code=404, detail='User not found. Operation rejected.')
    task_to_update = instance.execute(db.select(db.TaskT).where(db.TaskT.task_id == task_id)).scalar()
    if task_to_update is None: # Check if task exist
        raise HTTPException(status_code=404, detail='Task not found. Operation rejected.')
    is_user_owner = True if user_id == task_to_update.owner_id else None
    if is_user_owner is None:
        raise HTTPException(status_code=403, detail='Permission denied. This user does not have permission to update this task.')
    else:
        # Updating user information with model_dump() and setattr()
        update_data = params.model_dump(exclude_unset=True)
        [setattr(task_to_update, key, value) for key, value in update_data.items()]
        instance.commit()
    return task_to_update

@auth.delete('/tasks/delete/{task_id}', response_model=TaskDelete)
def delete_task(task_id: int, instance: Session = Depends(db.get_session)):
    """Delete task"""
    task_to_del = instance.execute(db.select(db.TaskT).where(db.TaskT.task_id == task_id)).scalar()
    if task_to_del is not None:
        instance.delete(task_to_del)
        instance.commit()
    else:
        raise HTTPException(status_code=404, detail='User not found. Operation rejected.')
    return task_to_del


# API comment endopoint

@auth.post('/tasks/comments/add', response_model=Comment)
def add_comment(user_id: int, task_id: int, comment: str, instance: Session = Depends(db.get_session)):
    """Add new comment in specific task"""
    user = instance.execute(db.select(db.UserT).where(db.UserT.user_id == user_id)).scalar()
    if user is None: # Checking if user exist
        raise HTTPException(status_code=404, detail='User not found. Operation rejected.')
    task = instance.execute(db.select(db.TaskT).where(db.TaskT.task_id == task_id)).scalar()
    if task is None: # Checking if task exist
        raise HTTPException(status_code=404, detail='Task not found. Operation rejected.')
    # Checking if user owns or is assigned to task
    is_assigned = [t.task_id for t in user.assigned_tasks if t.task_id == task.task_id]
    is_owned = [t.task_id for t in user.owned_tasks if t.task_id == task.task_id]
    if not (is_owned or is_assigned):
        raise HTTPException(status_code=403, detail='Permission denied. This user does not have permission to comment this task.')
    else:
        # Creating new comment, appending it to relationships list in task.comments finally commit
        new_comment = db.CommentT(user_id, task_id, comment)
        task.comments.append(new_comment)
        instance.add(task)
        instance.commit()
    return new_comment

@auth.post('/tasks/comments/update', response_model=Comment)
def update_comment(user_id: int, comment_id: int, params: CommentUpdate, instance: Session = Depends(db.get_session)):
    """Update comment"""
    user = instance.execute(db.select(db.UserT).where(db.UserT.user_id == user_id)).scalar()
    if user is None: # Checking if user exist
        raise HTTPException(status_code=404, detail='User not found. Operation rejected.')
    comment_to_update = instance.execute(db.select(db.CommentT).where(db.CommentT.comment_id == comment_id)).scalar()
    if comment_to_update is None: # Checking if user exist
        raise HTTPException(status_code=404, detail='Comment not found. Operation rejected.')
    if not user_id == comment_to_update.user_id:
        raise HTTPException(status_code=403, detail='Permission denied. This user does not have permission to update this comment.')
    else:
        update_data = params.model_dump(exclude_unset=True)
        [setattr(comment_to_update, key, value) for key, value in update_data.items()]
        instance.commit()
    return comment_to_update

@auth.delete('/tasks/comments/delete', response_model=CommentDelete)
def delete_comment(user_id: int, comment_id: int, instance: Session = Depends(db.get_session)):
    """Delete comment"""
    # Check if user exist
    user = instance.execute(db.select(db.UserT).where(db.UserT.user_id == user_id)).scalar()
    if user is None:
        raise HTTPException(status_code=404, detail='User not found. Operation rejected.')
    comment_to_del = instance.execute(db.select(db.CommentT).where(db.CommentT.comment_id == comment_id)).scalar()
    # Check if comment exist
    if comment_to_del is None:
        raise HTTPException(status_code=404, detail='Comment not found. Operation rejected.')
    
    instance.delete(comment_to_del)
    instance.commit()
    return comment_to_del



app.include_router(auth)