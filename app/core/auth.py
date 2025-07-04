from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session 
from app.db.user import User
from app.core.hashing import verify_password
from app.core.settings import settings
from app.db import db_session 
import jwt
from jwt import PyJWTError as JWTError


def authenticate_user(db: Session, email: str, password: str) -> bool | User:
    """
    verify whether the user exists in the database and if it exists check whether the password is correct
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict) -> str:
    """
    Generate a JWT token for the current user.
    Later this token will be associated with a rate limit based on the subscription
    and will also be used to fetch stock analysis data.
    """
    to_encode = data.copy()
    expires = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRY)
    to_encode.update({ 'exp': expires  })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_user(request: Request, session: Session):
    """
    Get the user associated with the JWT token from database
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Invalid authorization header"
        )
    
    # JWT token
    token = auth_header.split(" ")[1]   
    # Got the exception description from stackoverflow
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise exception
    except JWTError:
        raise exception

    user = session.query(User).filter(User.email == email).first()
    # If the token is invalid raise an exception for the user
    if user is None:
        raise exception
    return user
