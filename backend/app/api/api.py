# backend/app/api/api.py

from fastapi import APIRouter
from app.api.v1 import auth, users, search, movies, api_keys, oauth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(movies.router, prefix="/movies", tags=["movies"])
api_router.include_router(api_keys.router, prefix="/auth/api-keys", tags=["api-keys"])
api_router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])

# Import comments separately to handle potential import issues
try:
    from app.api.v1 import comments
    api_router.include_router(comments.router, prefix="/comments", tags=["comments"])
except ImportError as e:
    print(f"Warning: Could not import comments router: {e}")
    pass