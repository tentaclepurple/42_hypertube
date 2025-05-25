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
    Intercambiar API key + secret por Bearer token JWT
    
    Compatible con OAuth 2.0 grant_type=api_key
    """
    try:
        # Validar credenciales de API
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
        
        # Generar JWT token (reutiliza tu servicio existente)
        access_token = JWTService.create_access_token(
            user_id=user_info["user_id"],
            expires_delta=timedelta(hours=1)  # Token válido por 1 hora
        )
        
        return OAuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600,  # 1 hora en segundos
            scope="api"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating token: {str(e)}"
        )