# backend/app/api/v1/auth.py


from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.services.jwt_service import JWTService
from app.models.users import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.services.oauth_service import OAuthService
from app.services.jwt_service import JWTService
from app.db.session import get_db_connection
from app.services.supabase_services import supabase_service
from .queries import (update_existing_user,
                     update_existing_email,
                     insert_new_user)

import uuid
import secrets
from datetime import datetime

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
    

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login with username/email and password
    """
    try:
        # Authenticate user (verifica credenciales)
        user = await AuthService.authenticate_user(form_data.username, form_data.password)
        
        # Generate JWT token
        access_token = JWTService.create_access_token(user["id"])
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user["id"]),
                "email": user["email"],
                "username": user["username"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "profile_picture": user.get("profile_picture", "")
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/oauth/{provider}")
async def oauth_login(provider: str, request: Request):
    """
    Start OAuth flow with the specified provider
    """
    try:
        # Validate provider
        valid_providers = ["google", "github", "42"]
        if provider not in valid_providers:
            raise HTTPException(status_code=400, detail=f"Provider must be one of: {', '.join(valid_providers)}")
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # In a real app, you would store this state in a session or cookie
        # request.session["oauth_state"] = state
        
        # Generate redirect URI
        base_url = str(request.base_url).rstrip("/")
        redirect_uri = f"{base_url}api/v1/auth/oauth/{provider}/callback"
        
        # Get authorization URL
        auth_url = OAuthService.get_authorization_url(provider, redirect_uri, state)
        
        # Redirect user
        return RedirectResponse(auth_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")


@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str, state: str = None, request: Request = None):
    """
    Process OAuth callback from provider
    """
    try:
        # Validate provider
        valid_providers = ["google", "github", "42"]
        if provider not in valid_providers:
            raise HTTPException(status_code=400, detail=f"Provider must be one of: {', '.join(valid_providers)}")
        
        # In a real app, you would validate the state parameter
        # if state != request.session.get("oauth_state"):
        #     raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        # Generate redirect URI (must match the one used in authorization request)
        base_url = str(request.base_url).rstrip("/")
        redirect_uri = f"{base_url}/api/v1/auth/oauth/{provider}/callback"
        
        # Process callback and get user info
        user_info = await OAuthService.process_callback(provider, code, redirect_uri)
        
        # Download and upload profile picture if available
        profile_picture_url = user_info.get("profile_picture", "")
        if profile_picture_url:
            # Generate a temporary user ID if we don't have one yet
            temp_id = str(uuid.uuid4())
            
            # Download and upload to Supabase
            stored_url = await supabase_service.upload_profile_picture(
                profile_picture_url, 
                temp_id
            )
            
            # Update the profile picture URL
            if stored_url:
                user_info["profile_picture"] = stored_url
        
        # Now we need to create or update the user in our database
        async with get_db_connection() as conn:
            # Check if user already exists by OAuth ID
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE oauth_provider = $1 AND oauth_id = $2",
                user_info["oauth_provider"], user_info["oauth_id"]
            )
            
            if user:
                # User exists, update information if needed
                await conn.execute(update_existing_user,
                    user_info["first_name"], user_info["last_name"], 
                    user_info["profile_picture"], datetime.now(),
                    user_info["oauth_provider"], user_info["oauth_id"]
                )
                
                # Fetch updated user
                user = await conn.fetchrow(
                    "SELECT * FROM users WHERE oauth_provider = $1 AND oauth_id = $2",
                    user_info["oauth_provider"], user_info["oauth_id"]
                )
            else:
                # Check if email already exists
                email_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM users WHERE email = $1)",
                    user_info["email"]
                )
                
                if email_exists:
                    # Link existing account with OAuth provider
                    await conn.execute(update_existing_email,
                        user_info["oauth_provider"], user_info["oauth_id"],
                        user_info["first_name"], user_info["last_name"], 
                        user_info["profile_picture"], datetime.now(), 
                        user_info["email"]
                    )
                    
                    # Fetch updated user
                    user = await conn.fetchrow(
                        "SELECT * FROM users WHERE email = $1",
                        user_info["email"]
                    )
                else:
                    # Check if username exists
                    username_exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM users WHERE username = $1)",
                        user_info["username"]
                    )
                    
                    # Create new user ID
                    user_id = uuid.uuid4()
                    
                    # If username exists, create a unique one
                    username = user_info["username"]
                    if username_exists:
                        username = f"{username}_{user_id.hex[:6]}"
                    
                    # Insert new user
                    user = await conn.fetchrow(insert_new_user,
                        user_id, user_info["email"], username, 
                        user_info["first_name"], user_info["last_name"], 
                        user_info["profile_picture"], 
                        user_info["oauth_provider"], user_info["oauth_id"], 
                        datetime.now()
                    )
            
        access_token = JWTService.create_access_token(user["id"])
    
            # Create a response with the token
        response = JSONResponse(
                content={
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": {
                        "id": str(user["id"]),
                        "email": user["email"],
                        "username": user["username"],
                        "first_name": user["first_name"],
                        "last_name": user["last_name"],
                        "profile_picture": user["profile_picture"] if user.get("profile_picture") else ""
                    }
                }
            )
        
        return response
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")