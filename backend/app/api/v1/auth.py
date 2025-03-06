# backend/app/api/v1/auth.py


from fastapi import APIRouter, HTTPException
from app.models.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(user_data: UserCreate):
    """
    Register a new user with email and password.
    """
    try:
        user = await AuthService.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # In production, you would want to log this error
        raise HTTPException(status_code=500, detail="An error occurred while registering the user")
