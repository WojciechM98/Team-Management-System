from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from jwt import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os 
from dotenv import load_dotenv

import db
from pwhshr import PasswordHash


load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

# Security tables
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class User(BaseModel):
    username: str
    email: str 
    disabled: bool 
    
class UserInDB(User):
    hashed_password: str

def get_user_by_email(email: str, instance: Session):
    # Check if user with given email exist (user_id not used in security 
    # because loging in with email and password)
    user = instance.execute(db.select(db.UserT).where(db.UserT.email == email)).scalar()
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    else:
        return user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return PasswordHash.check(plain_password, hashed_password)

def get_password_hash(password: str) -> PasswordHash:
    return PasswordHash.new(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(email: str, password: str, instance: Session):
    """Loging with email and password"""
    user = get_user_by_email(email, instance)
    if not user:
        return False
    if not verify_password(password, user.password.hash):
        return False
    return user



async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], 
                           instance: Session = Depends(db.get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get('sub')
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user_by_email(token_data.email, instance)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.disabled: # In db user.disable must be true to work
        raise HTTPException(status_code=400, detail='Inactive user')

def login_for_access_token_function(form_data: OAuth2PasswordRequestForm, instance: Session):
    user = authenticate_user(form_data.username, form_data.password, instance) # NOTE: Here search in DB for account (by email or name)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user.email}, expires_delta=access_token_expires
    ) # For 'sub': user.email because email is used to login
    return Token(access_token=access_token, token_type='bearer')