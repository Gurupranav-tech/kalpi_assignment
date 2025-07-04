from typing import Literal
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import EmailType
from pydantic import BaseModel, EmailStr


Base = declarative_base()

class User(Base):
    """
    Users Class(ORM) that interfaces the database
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, index=True, nullable=False)
    email = Column(EmailType, index=True, unique=True, nullable=False)
    password = Column(String, nullable=False)
    tier = Column(String, default="free", nullable=False)


"""
These classes are pydantic classes for FastAPI to do data validation
"""
class UserAuthLogin(BaseModel):
    email: EmailStr
    password: str


class UserAuthSignin(BaseModel):
    username: str
    email: EmailStr
    password: str
    tier: Literal["free", "pro", "premium"]
