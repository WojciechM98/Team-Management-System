from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, joinedload, Session
from sqlalchemy import Date, func, null, select, exists
from sqlalchemy import ForeignKey, Table, Column, String, Integer, CHAR, JSON
import datetime

DATABASE_URL = 'postgresql://postgres:1234@localhost/postgres'

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
    Column('task_id', Integer, ForeignKey('tasks.task_id', ondelete='CASCADE'), primary_key=True)
)

def create_comment(user_id: int, comment: str):
    return {'user_id': user_id,
            'timestamp': func.now(),
            'comment': comment}

class UserT(Base):
    __tablename__ = 'users'
    user_id = Column('user_id', Integer, primary_key=True, autoincrement=True)
    user_name = Column('user_name', String)

    # Many-to-Many relationship. User can be assigned to many tasks 
    # lazy='joined' used to reload relations every time form database
    assigned_tasks = relationship('TaskT', secondary=user_task_association, back_populates='assigned_users', lazy='joined')
    # One-to-Many relationship. User can create many tasks
    # Note: Deleting a user deletes the tasks he created
    owned_tasks = relationship('TaskT', back_populates='task_owner', lazy='joined', cascade='all, delete-orphan')

    def __init__(self, user_name):
        self.user_name = user_name

    def __repr__(self):
        tasks_info = [(task.task_id, task.title) for task in self.owned_tasks]
        return f'<User (user ID: {self.user_id}, user name: {self.user_name}, user owned tasks: {tasks_info}, user assigned tasks: {[task.task_id for task in self.assigned_tasks]})>'

class TaskT(Base):
    __tablename__ = 'tasks'
    task_id = Column('task_id', Integer, primary_key=True, autoincrement=True)

    # TODO: IDK if i need created_by_user_id - this can be obtained from 'task_owner.user_id' in FastAPI
    created_by_user_id = Column('created_by', Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=True)
    start_date = Column('start_date', Date, server_default=func.now())
    end_date = Column('end_time', Date, nullable=True)
    title = Column('title', String)
    description = Column('description', String, nullable=True)
    comments = Column('comments', JSON, nullable=True)
    
    # Many_to_Many relationship. Task can have assigned multiple users
    assigned_users = relationship('UserT', secondary=user_task_association, back_populates='assigned_tasks', lazy='joined')
    # Many-to-One relationship. Task can have only one creator
    task_owner = relationship('UserT', back_populates='owned_tasks', lazy='joined')

    def __init__(self, created_by_user_id, title, description = None):
        self.created_by_user_id = created_by_user_id
        self.title = title
        self.description = description

    # TODO: Function to set date for end_date and optionaly for start_date
    def set_date(self):
        end_date = func.now()

    def __repr__(self):
        created_by = f'{self.task_owner.user_id} {self.task_owner.user_name}'
        return (f'<Task (title: {self.title}, task ID: {self.task_id}, '
                f'start date: {self.start_date}, end date: {self.end_date}, '
                f'created by user: {self.created_by_user_id})>\n')

# TODO: Create error hangler for commiting changes 
class CommitHandler():
    def __init__(self, session: sessionmaker):
        self.session = session

# Create columns
Base.metadata.create_all(bind=engine)

# TODO: Create object for safe error rising 
# CommitHandler(session=session)

# session = Session()
# user1 = UserT('Wojtek')
# user2 = UserT('Piotr')
# task1 = TaskT(1, 'Task 1')
# task2 = TaskT(1, 'Task 2')
# task3 = TaskT(2, 'Task 3')

# task1.assigned_users.extend([user1, user2])
# task2.assigned_users.append(user2)
# task3.assigned_users.append(user1)
# session.add(user1)
# session.add(user2)
# session.add(task1)
# session.add(task2)
# session.add(task3)

# session.commit()

# results = session.query(TaskT).all()
# print(results)
# results = session.query(UserT).all()
# print(results)

