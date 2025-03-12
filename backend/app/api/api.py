# backend/app/api/api.py

from fastapi import APIRouter
from app.api.v1 import auth, users, search, movies

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(movies.router, prefix="/movies", tags=["movies"])