# backend/app/api/deps.py


from fastapi import Depends, HTTPException, status, Cookie, Request, Header, Query
from fastapi.security import OAuth2PasswordBearer
from app.services.jwt_service import JWTService
from app.services.token_service import TokenService
from app.db.session import get_db_connection
from typing import Optional
import uuid


# Define the token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current authenticated user
    """
    try:
        # Verify if the token is revoked
        is_revoked = await TokenService.is_token_revoked(token)
        if is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify the token
        user_id = JWTService.verify_token(token)
        
        # Get user from database
        async with get_db_connection() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, username, first_name, last_name, profile_picture FROM users WHERE id = $1",
                uuid.UUID(user_id)
            )
            
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return dict(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_from_cookie(request: Request):
    """Get user from cookie instead of Authorization header"""
    token = request.cookies.get("access_token")
            
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication cookie required"
        )

    try:
        is_revoked = await TokenService.is_token_revoked(token)
        if is_revoked:
            raise HTTPException(401, "Token has been revoked")
        
        user_id = JWTService.verify_token(token)
        
        async with get_db_connection() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, username, first_name, last_name, profile_picture FROM users WHERE id = $1",
                uuid.UUID(user_id)
            )
            
        if not user:
            raise HTTPException(401, "Could not validate credentials")
        
        return dict(user)
    except ValueError as e:
        raise HTTPException(401, str(e))


async def get_current_user_hybrid(
    request: Request,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    """
    Hybrid authentication: tries Authorization header first, then cookie, then query param
    """
    auth_token = None
    auth_method = None
    # Try Authorization header first
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.replace("Bearer ", "")
        auth_method = "header"
    # Try query parameter token (for video streaming)
    elif token:  # ← ADD THIS BLOCK
        auth_token = token
        auth_method = "query"
    # Fallback to cookie
    else:
        auth_token = request.cookies.get("access_token")
        if auth_token:
            auth_method = "cookie"
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token provided"
        )
    try:
        is_revoked = await TokenService.is_token_revoked(auth_token)
        if is_revoked:
            raise HTTPException(401, "Token has been revoked")
        user_id = JWTService.verify_token(auth_token)
        async with get_db_connection() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, username, first_name, last_name, profile_picture FROM users WHERE id = $1",
                uuid.UUID(user_id)
            )
        if not user:
            raise HTTPException(401, "Could not validate credentials")
        print(f"DEBUG: ✓ User authenticated via {auth_method}: {user['username']}", flush=True)
        return dict(user)
    except ValueError as e:
        print(f"DEBUG: ✗ Token validation error: {str(e)}", flush=True)
        raise HTTPException(401, str(e))