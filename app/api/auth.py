from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.hashing import hash_password, verify_password
from app.db import db_session
from app.db.user import User, UserAuthLogin, UserAuthSignin
from app.core import auth
from . import router


@router.post(
    "/login",
    summary="Login and get JWT token",
    description="Authenticate with email and password to receive a JWT token which can be used to request dtock analysis data from the server based on the subsciption that was used to create the token. Note that a JWT token is only valid for 1 hour",
    tags=["auth"]
)
async def login(user: UserAuthLogin, session: Session = Depends(db_session)):
    userdb = session.query(User).filter(User.email == user.email).first()
    if not userdb or not verify_password(user.password, userdb.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")
    jwt = auth.create_access_token({ "sub": userdb.email  })
    return { "token": jwt  }

@router.post(
    "/register",
    summary="Register new user",
    description="Create a new user with email username and tier based on subscription",
    tags=["auth"]
)
async def register(data: UserAuthSignin, session: Session = Depends(db_session)):
    user = session.query(User).filter(User.email == data.email).first()
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    hashed_password = hash_password(data.password)
    user = User(username=data.username, email=data.email, password=hashed_password, tier=data.tier)
    session.add(user)
    session.commit()
    session.refresh(user)
    return { "status": "User created successfully"  }
