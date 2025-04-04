from fastapi import FastAPI, HTTPException, Depends, APIRouter
from pydantic import BaseModel, Field, model_serializer
from typing import Optional, List, Annotated
import datetime
from sqlalchemy.orm import Session
import db
from pwhshr import Password, PasswordHash
from schemas import *
import security as sc

def find_user_in_db(user_id: int, instance: Session) -> User:
    """Check if user with user_id exist in database and return user. 
    If user doesn't exist then raise HTTPException"""
    user = instance.execute(db.select(db.UserT).where(db.UserT.user_id == user_id)).scalar()
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    return user

def find_task_in_db(task_id: int, instance: Session) -> Task:
    """Check if task with task_id exist in database and return task.
    If task doesn't exist then raise HTTPException"""
    task = instance.execute(db.select(db.TaskT).where(db.TaskT.task_id == task_id)).scalar()
    if task is None:
        raise HTTPException(status_code=404, detail='Task not found')
    return task

def find_comment_in_db(comment_id: int, instance: Session) -> Comment:
    """Check if comment with comment_id exist in database and return comment.
    If comment doesn't exist then raise HTTPException"""
    comment = instance.execute(db.select(db.CommentT).where(db.CommentT.comment_id == comment_id)).scalar()
    if comment is None:
        raise HTTPException(status_code=404, detail='Comment not found')
    return comment

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
    user = find_user_in_db(user_id, instance=instance)
    return user

@app.post('/users/add', response_model=User)
def create_user(username: str, email: str, password: str, instance: Session = Depends(db.get_session)):
    """Create new user db.UserT class by passing UserCreate variables"""
    new_user = db.UserT(username, email, password)
    instance.add(new_user)
    instance.commit()
    return new_user

@auth.post('/users/update', response_model=User)
def update_user(user_id: int, params: UserUpdate, instance: Session = Depends(db.get_session)):
    """Update user"""
    user_to_update = find_user_in_db(user_id, instance=instance)
    # Updating user information with model_dump() and setattr()
    update_data = params.model_dump(exclude_unset=True)
    [setattr(user_to_update, key, value) for key, value in update_data.items()]
    instance.commit()
    return user_to_update

@auth.delete('/users/delete/{user_id}', response_model=UserDelete)
def delete_user(user_id: int, instance: Session = Depends(db.get_session)):
    """Delete user by entering his ID and tasks that he owns"""
    user_to_del = find_user_in_db(user_id, instance=instance)
    instance.delete(user_to_del)
    instance.commit()
    return user_to_del


# API task endpoints

@auth.get('/tasks', response_model=List[Task])
def get_tasks(instance: Session = Depends(db.get_session)):
    """Return all tasks"""
    tasks = instance.execute(db.select(db.TaskT)).unique().scalars()
    result = [task for task in tasks]
    return result

@auth.get('/tasks/{task_id}', response_model=Task)
def get_task(task_id: int, instance: Session = Depends(db.get_session)):
    """Return one task by entering task ID"""
    task = find_task_in_db(task_id, instance=instance)
    return task

@auth.post('/tasks/add', response_model=Task)
def add_task(user_id: int, title: str, description: str, instance: Session = Depends(db.get_session)):
    """Add new task"""
    find_user_in_db(user_id, instance=instance)
    new_task = db.TaskT(user_id, title, description)
    instance.add(new_task)
    instance.commit()
    return new_task

@auth.post('/tasks/assign', response_model=Task)
def assign_user_to_task(owner_id: int, task_id: int, user_id_to_assign: int, instance: Session = Depends(db.get_session)):
    """Assign user to task"""
    find_user_in_db(owner_id, instance=instance)
    user_to_assign = find_user_in_db(user_id_to_assign, instance=instance)
    task = find_task_in_db(task_id, instance=instance)
    task.assigned_users.append(user_to_assign)
    instance.commit()
    return task

@auth.post('/tasks/update', response_model=Task)
def update_task(owner_id: int, task_id: int, params: TaskUpdate, instance: Session = Depends(db.get_session)):
    """Update task"""
    find_user_in_db(owner_id, instance=instance)
    task_to_update = find_task_in_db(task_id, instance=instance)
    is_user_owner = True if owner_id == task_to_update.owner_id else False
    if is_user_owner is False:
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
    task_to_del = find_task_in_db(task_id, instance=instance)
    instance.delete(task_to_del)
    instance.commit()
    return task_to_del


# API comment endopoint

@auth.post('/tasks/comments/add', response_model=Comment)
def add_comment(user_id: int, task_id: int, comment: str, instance: Session = Depends(db.get_session)):
    """Add new comment in specific task"""
    user = find_user_in_db(user_id, instance=instance)
    task = find_task_in_db(task_id, instance=instance)
    # Checking if user owns or is assigned to task
    is_assigned = [t.task_id for t in user.assigned_tasks if t.task_id == task.task_id]
    is_owned = [t.task_id for t in user.owned_tasks if t.task_id == task.task_id]
    if not (is_owned or is_assigned):
        raise HTTPException(status_code=403, detail='Permission denied. This user does not have permission to comment this task.')
    # Creating new comment, appending it to relationships list in task.comments finally commit
    new_comment = db.CommentT(user_id, task_id, comment)
    task.comments.append(new_comment)
    instance.add(task)
    instance.commit()
    return new_comment

@auth.post('/tasks/comments/update', response_model=Comment)
def update_comment(user_id: int, comment_id: int, params: CommentUpdate, instance: Session = Depends(db.get_session)):
    """Update comment"""
    find_user_in_db(user_id, instance=instance)
    comment_to_update = find_comment_in_db(comment_id, instance=instance)
    if not user_id == comment_to_update.user_id:
        raise HTTPException(status_code=403, detail='Permission denied. This user does not have permission to update this comment.')
    update_data = params.model_dump(exclude_unset=True)
    [setattr(comment_to_update, key, value) for key, value in update_data.items()]
    instance.commit()
    return comment_to_update

@auth.delete('/tasks/comments/delete', response_model=CommentDelete)
def delete_comment(user_id: int, comment_id: int, instance: Session = Depends(db.get_session)):
    """Delete comment"""
    # Check if user exist
    user = find_user_in_db(user_id, instance=instance)
    comment_to_del = find_comment_in_db(comment_id, instance=instance)
    instance.delete(comment_to_del)
    instance.commit()
    return comment_to_del



app.include_router(auth)