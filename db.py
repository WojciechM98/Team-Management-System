from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, relationship, joinedload, Session, validates
from sqlalchemy import Date, DateTime, func, null, select, exists, insert, update
from sqlalchemy import ForeignKey, Table, Column, String, Integer, CHAR, JSON
from typing import Optional, List
import datetime
from pwhshr import Password
import os
from dotenv import load_dotenv

load_dotenv(override=True)
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_URL = f'postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@localhost/postgres'

engine = create_engine(DATABASE_URL, echo=True)

Base = declarative_base()

# Session class
Session = sessionmaker(bind=engine)
# Creating one session instance because only this app works with database,
# so every change is created in this session instance. 
# In case of multiple acesses to the database better create new session 
# when calling endpoint


def get_session():
    db = Session()
    try:
        yield db
    finally:
        db.close()

# Association table (Many to Many)
user_task_association = Table(
    'user_task_association', 
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True),
    Column('task_id', Integer, ForeignKey('tasks.task_id', ondelete='CASCADE'), primary_key=True))

class UserT(Base):
    __tablename__ = 'users'
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    password: Mapped[str] = mapped_column(Password)
    email: Mapped[str]

    # Many-to-Many relationship. User can be assigned to many tasks 
    # lazy='joined' used to reload relations every time form database
    assigned_tasks: Mapped[Optional[List['TaskT']]] = relationship(secondary=user_task_association, back_populates='assigned_users', lazy='joined')
    # One-to-Many relationship. User can create many tasks
    # Note: Deleting a user deletes the tasks he created
    owned_tasks: Mapped[Optional[List['TaskT']]] = relationship(back_populates='task_owner', lazy='joined', cascade='all, delete-orphan')

    # TODO: Create reletionship for Assigned tasks (done), Owned tasks (done), Comments (todo) to make for
    # future GUI app easier to search for assigned and created things. Maybe after loging create instance 
    # of a user with easy access to relationships and nested informations (comments etc.). Maybe create 
    # new endpoint get_user_info and return every information, every relationship for this specific user.

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    def __repr__(self):
        owned = [(task.task_id, task.title) for task in self.owned_tasks]
        assigned = [task.task_id for task in self.assigned_tasks]
        return f'<User (user ID: {self.user_id}, user name: {self.username}, '\
               f'user password: {self.password} user owned tasks: {owned}, '\
               f'user assigned tasks: {assigned})>\n'


class TaskT(Base):
    __tablename__ = 'tasks'
    task_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # TODO: IDK if i need owner_id - this can be obtained from 'task_owner.user_id' in FastAPI
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'))
    start_date: Mapped[datetime.date] = mapped_column(server_default=func.now())
    end_date: Mapped[Optional[datetime.date]] = mapped_column(nullable=True)
    title: Mapped[str]
    description: Mapped[str] = mapped_column(nullable=True)
    comments: Mapped[Optional[List['CommentT']]] = relationship(cascade='all, delete-orphan')
    
    # Many-to-One relationship. Task can have only one creator
    task_owner: Mapped['UserT'] = relationship(back_populates='owned_tasks', lazy='joined')
    # Many_to_Many relationship. Task can have assigned multiple users
    assigned_users: Mapped[Optional[List['UserT']]] = relationship(secondary=user_task_association, back_populates='assigned_tasks', lazy='joined')

    def __init__(self, user_id, title, description = None):
        self.owner_id = user_id
        self.title = title
        self.description = description

    # TODO: Function to set date for end_date and optionaly for start_date
    def set_date(self):
        return func.now()

    def __repr__(self):
        assigned = [user.user_id for user in self.assigned_users]
        return (f'<Task (task ID: {self.task_id}, title: {self.title}, description: {self.description}, '
                f'start date: {self.start_date}, end date: {self.end_date}, '
                f'owner: {self.owner_id}, assigned users: {assigned}, '
                f'comments: {self.comments})>\n')

class CommentT(Base):
    __tablename__ = "comments"
    comment_id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.task_id', ondelete='CASCADE'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'))
    timestamp: Mapped[datetime.datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    comment: Mapped[str]

    def __init__(self, user_id: int, task_id: int, comment: str):
        self.user_id = user_id
        self.task_id = task_id
        self.comment = comment
    
    def __repr__(self):
        return f'<Comment (id: {self.comment_id}, task_id: {self.task_id}, timestamp: {self.timestamp}, comment: {self.comment})>\n'

# TODO: Create error hangler for commiting changes 
class CommitHandler():
    def __init__(self, session: sessionmaker):
        self.session = session

# Create columns
Base.metadata.create_all(bind=engine)

