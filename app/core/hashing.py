"""
This file will consist of all the password hashing and token generation.
This is so that in future if we need to use a different hashing algorithm like argon there is just one file o change
"""
from passlib.context import CryptContext


hasher = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    return hasher.verify(plain, hashed)


def hash_password(password: str) -> str:
    return hasher.hash(password)
