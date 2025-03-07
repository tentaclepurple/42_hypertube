# backend/app/api/deps.py


from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.services.jwt_service import JWTService
from app.db.session import get_db_connection
import uuid


# Define the token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current authenticated user
    
    Args:
        token: JWT token from the request
        
    Returns:
        dict: User information
        
    Raises:
        HTTPException: If token is invalid or user doesn't exist
    """
    try:
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