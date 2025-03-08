# backend/app/api/v1/users.py


from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status, Request
from typing import Optional
from pydantic import BaseModel, Field, validator
from app.api.deps import get_current_user
from app.db.session import get_db_connection
from app.services.supabase_services import supabase_service
from app.models.users import ProfileUpdate
import uuid
import os
from datetime import datetime
import json

router = APIRouter()


@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
    ):
    """
    Update user profile
    """
    try:
        # Usar el ID directamente sin intentar convertirlo a UUID de Python
        user_id = current_user["id"]
        
        # Verificar si los IDs de películas existen en la base de datos
        movie_ids = [
            profile_data.favorite_movie_id,
            profile_data.worst_movie_id,
            profile_data.movie_preference_a_id,
            profile_data.movie_preference_b_id,
            profile_data.movie_preference_c_id,
            profile_data.movie_preference_d_id
        ]
        
        # Filtrar IDs no nulos
        valid_movie_ids = [id for id in movie_ids if id is not None]
        
        if valid_movie_ids:
            async with get_db_connection() as conn:
                # Verificar que todas las películas referenciadas existen
                for movie_id in valid_movie_ids:
                    movie_exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM movies WHERE id = $1)",
                        movie_id
                    )
                    if not movie_exists:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Movie with ID {movie_id} does not exist"
                        )
        
        # Usar la imagen de perfil existente
        profile_picture_url = current_user.get("profile_picture", "")
        
        # Si no hay imagen de perfil, asignar una por defecto
        if not profile_picture_url:
            profile_picture_url = "https://ujbctboiqjsoskaflslz.supabase.co/storage/v1/object/public/profile_images//burp.png"
        
        # Verificar si el email ya está en uso (si se proporciona)
        if profile_data.email and profile_data.email != current_user["email"]:
            async with get_db_connection() as conn:
                email_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM users WHERE email = $1 AND id != $2)",
                    profile_data.email, user_id
                )
                
                if email_exists:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email is already in use by another account"
                    )
        
        # Actualizar el perfil en la base de datos
        async with get_db_connection() as conn:
            # Verificar si es la primera vez que se completa el perfil
            is_profile_completed = await conn.fetchval(
                "SELECT profile_completed FROM users WHERE id = $1",
                user_id
            )
            
            # Preparar los datos para la actualización
            update_data = {
                "birth_year": profile_data.birth_year,
                "gender": profile_data.gender,
                "favorite_movie_id": profile_data.favorite_movie_id,
                "worst_movie_id": profile_data.worst_movie_id,
                "movie_preference_a_id": profile_data.movie_preference_a_id,
                "movie_preference_b_id": profile_data.movie_preference_b_id,
                "movie_preference_c_id": profile_data.movie_preference_c_id,
                "movie_preference_d_id": profile_data.movie_preference_d_id,
                "profile_picture": profile_picture_url,
                "updated_at": datetime.now()
            }
            
            # Si se proporciona email, incluirlo en la actualización
            if profile_data.email:
                update_data["email"] = profile_data.email
            
            # Verificar si todos los campos requeridos están completos
            profile_is_complete = all([
                profile_data.birth_year,
                profile_data.gender,
                profile_data.favorite_movie_id,
                profile_data.worst_movie_id
            ])
            
            if profile_is_complete:
                update_data["profile_completed"] = True
            
            # Construir la consulta de actualización dinámicamente
            set_clauses = ", ".join([f"{key} = ${i+1}" for i, key in enumerate(update_data.keys())])
            values = list(update_data.values())
            
            # Añadir el ID del usuario como último parámetro
            query = f"UPDATE users SET {set_clauses} WHERE id = ${len(values)+1} RETURNING *"
            values.append(user_id)
            
            # Ejecutar la actualización
            updated_user = await conn.fetchrow(query, *values)
            
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verificar si se completaron todos los campos requeridos
            if not profile_is_complete:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Profile update successful but some required fields are missing"
                )
            
            # Devolver los datos del usuario actualizados
            return {
                "id": str(updated_user["id"]),
                "username": updated_user["username"],
                "email": updated_user["email"],
                "first_name": updated_user["first_name"],
                "last_name": updated_user["last_name"],
                "profile_picture": updated_user["profile_picture"],
                "birth_year": updated_user["birth_year"],
                "gender": updated_user["gender"],
                "favorite_movie_id": str(updated_user["favorite_movie_id"]) if updated_user["favorite_movie_id"] else None,
                "worst_movie_id": str(updated_user["worst_movie_id"]) if updated_user["worst_movie_id"] else None,
                "profile_completed": updated_user["profile_completed"],
                "message": "Profile updated successfully"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )


@router.put("/profile/image")
async def update_profile_image(
    profile_picture: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
    ):
    """
    Update user profile picture
    """
    try:
        user_id = current_user["id"]
        
        try:
            file_content = await profile_picture.read()
            print(f"Read file content, size: {len(file_content)} bytes", flush=True)
        except Exception as e:
            print(f"Error reading file: {e}", flush=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error reading uploaded file: {str(e)}"
            )
        
        try:
            profile_picture_url = await supabase_service.update_profile_picture(
                file_content,
                str(user_id)
            )
            
            if not profile_picture_url:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to upload profile picture"
                )
        except Exception as e:
            print(f"Error uploading to Supabase: {e}", flush=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading profile picture: {str(e)}"
            )
        
        try:
            async with get_db_connection() as conn:
                updated_user = await conn.fetchrow(
                    "UPDATE users SET profile_picture = $1, updated_at = $2 WHERE id = $3 RETURNING id, profile_picture",
                    profile_picture_url, datetime.now(), user_id
                )
                
                if not updated_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                
                print(f"Updated user record with new profile picture", flush=True)
        except Exception as e:
            print(f"Database error: {e}", flush=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user record: {str(e)}"
            )
        
        return {
            "profile_picture": profile_picture_url,
            "message": "Profile picture updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {e}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile picture: {str(e)}"
        )
