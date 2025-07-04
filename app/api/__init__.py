"""
Standard organization of a python app
"""
from fastapi import APIRouter


router = APIRouter()

from . import auth
from . import data
