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

class ProfileUpdateForm(BaseModel):
    profile_data: str


@router.put("/profile")
async def update_profile(
    request: Request,
    profile_picture: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
    ):
    print("KKKKKKKKKKKKKKKKKK", request, flush=True)

    form_data = await request.form()
    print("FFFF", form_data, flush=True)
    profile_data_str = form_data.get("profile_data")
    print("**PPPP", profile_data_str, flush=True)
    print(">>", type(profile_picture), flush=True)
    
    if not profile_data_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="profile_data is required"
        )
    try:
        profile_data = json.loads(profile_data_str)
        profile_update = ProfileUpdate(**profile_data)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid profile data: {str(e)}"
        )
    """
    Update user profile
    """
    try:
        print("--------------------")
        user_id = uuid.UUID(current_user["id"])
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
        
        # Manejar la subida de imagen de perfil
        profile_picture_url = current_user.get("profile_picture", "")
        
        if profile_picture:
            # Si hay una imagen existente, eliminarla
            if profile_picture_url and "profile_pictures" in profile_picture_url:
                try:
                    file_name = profile_picture_url.split("/")[-1]
                    supabase_service.client.storage.from_('profile_pictures').remove([file_name])
                except Exception as e:
                    print(f"Error removing old profile picture: {str(e)}")
            
            # Subir la nueva imagen
            try:
                profile_picture_url = await supabase_service.upload_profile_picture(
                    profile_picture.file.read(),
                    str(user_id)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error uploading profile picture: {str(e)}"
                )
        
        # Si este es un perfil nuevo y no se proporciona imagen, asignar una por defecto
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
                "bio": profile_data.bio,
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
                
                # Si es la primera vez que se completa, registrar la fecha
                if not is_profile_completed:
                    update_data["profile_completed_at"] = datetime.now()
            
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
                "bio": updated_user["bio"],
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






""" @router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    profile_picture: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
    ):
    print("KKKKKKKKKKKKKKKKKK", flush=True)

    try:
        user_id = uuid.UUID(current_user["id"])
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
        
        # Manejar la subida de imagen de perfil
        profile_picture_url = current_user.get("profile_picture", "")
        
        if profile_picture:
            # Si hay una imagen existente, eliminarla
            if profile_picture_url and "profile_pictures" in profile_picture_url:
                try:
                    file_name = profile_picture_url.split("/")[-1]
                    supabase_service.client.storage.from_('profile_pictures').remove([file_name])
                except Exception as e:
                    print(f"Error removing old profile picture: {str(e)}")
            
            # Subir la nueva imagen
            try:
                profile_picture_url = await supabase_service.upload_profile_picture(
                    profile_picture.file.read(),
                    str(user_id)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error uploading profile picture: {str(e)}"
                )
        
        # Si este es un perfil nuevo y no se proporciona imagen, asignar una por defecto
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
                "bio": profile_data.bio,
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
                
                # Si es la primera vez que se completa, registrar la fecha
                if not is_profile_completed:
                    update_data["profile_completed_at"] = datetime.now()
            
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
                "bio": updated_user["bio"],
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
        ) """