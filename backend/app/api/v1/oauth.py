# backend/app/api/v1/oauth.py

from fastapi import APIRouter, HTTPException, status
from app.models.api_key import OAuthTokenRequest, OAuthTokenResponse
from app.services.api_key_service import ApiKeyService
from app.services.jwt_service import JWTService
from datetime import timedelta

router = APIRouter()


@router.post("/token", response_model=OAuthTokenResponse)
async def oauth_token(token_request: OAuthTokenRequest):
    """
    Exchange API credentials for a JWT token
    
    """
    try:
        # Validate API credentials
        user_info = await ApiKeyService.validate_api_credentials(
            api_key=token_request.api_key,
            api_secret=token_request.api_secret
        )
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generate JWT token (reuse your existing service)
        access_token = JWTService.create_access_token(
            user_id=user_info["user_id"],
            expires_delta=timedelta(hours=1)  # Token valid for 1 hour
        )
        
        return OAuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600,  # 1 hour in seconds
            scope="api"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating token: {str(e)}"
        )