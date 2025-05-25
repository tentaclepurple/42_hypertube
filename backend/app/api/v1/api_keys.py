# backend/app/api/v1/api_keys.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.api.deps import get_current_user
from app.models.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyListResponse
from app.services.api_key_service import ApiKeyService

router = APIRouter()


@router.post("/", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Crear una nueva API key para el usuario autenticado
    """
    try:
        user_id = current_user["id"]
        
        result = await ApiKeyService.create_api_key(
            user_id=str(user_id),
            name=api_key_data.name,
            expires_in_days=api_key_data.expires_in_days or 30
        )
        
        return ApiKeyResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating API key: {str(e)}"
        )


@router.get("/", response_model=List[ApiKeyListResponse])
async def get_user_api_keys(
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener todas las API keys del usuario autenticado
    """
    try:
        user_id = str(current_user["id"])
        
        api_keys = await ApiKeyService.get_user_api_keys(user_id)
        
        return [ApiKeyListResponse(**key) for key in api_keys]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving API keys: {str(e)}"
        )


@router.patch("/{api_key_id}/revoke")
async def revoke_api_key(
    api_key_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Revocar (desactivar) una API key
    """
    try:
        user_id = str(current_user["id"])
        
        success = await ApiKeyService.revoke_api_key(user_id, api_key_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or not owned by user"
            )
        
        return {"message": "API key revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revoking API key: {str(e)}"
        )


@router.delete("/{api_key_id}")
async def delete_api_key(
    api_key_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Eliminar completamente una API key
    """
    try:
        user_id = str(current_user["id"])
        
        success = await ApiKeyService.delete_api_key(user_id, api_key_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or not owned by user"
            )
        
        return {"message": "API key deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting API key: {str(e)}"
        )