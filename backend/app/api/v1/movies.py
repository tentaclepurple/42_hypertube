# backend/app/api/v1/movies.py

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from typing import List, Optional
from datetime import datetime
import json
import time
import uuid

from app.api.deps import get_current_user
from app.db.session import get_db_connection
from app.models.movie import MovieDetail, MovieSearchResponse, DownloadRequest
from app.models.view_progress import ViewProgressUpdate, ViewProgressResponse
from app.services.imdb_graphql_service import IMDBGraphQLService
from app.services.kafka_service import kafka_service

from fastapi.responses import StreamingResponse
import aiofiles
import os


router = APIRouter()


@router.get("/{movie_id}", response_model=MovieDetail)
async def get_movie_details(
    movie_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene detalles completos de una película, incluyendo información de APIs externas si es necesario
    e información de visualización del usuario
    """
    try:
        user_id = current_user["id"]
        
        # Buscar la película en la base de datos con información de visualización
        async with get_db_connection() as conn:
            movie = await conn.fetchrow(
                """
                SELECT 
                    m.*,
                    COALESCE(umv.view_percentage, 0.0) as view_percentage,
                    COALESCE(umv.completed, false) as completed
                FROM movies m
                LEFT JOIN user_movie_views umv ON m.id = umv.movie_id AND umv.user_id = $2
                WHERE m.id = $1
                """, 
                uuid.UUID(movie_id),
                user_id
            )
            
            if not movie:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Movie not found"
                )
                
            movie_dict = dict(movie)
            
            # Verificar si necesitamos obtener información adicional
            needs_additional_info = (
                not movie_dict.get("director") or 
                len(movie_dict.get("director", [])) == 0 or
                not movie_dict.get("casting") or
                len(movie_dict.get("casting", [])) == 0
            )
            
            # Si necesitamos información adicional y tenemos el imdb_id
            if needs_additional_info and movie_dict.get("imdb_id"):
                print(f"Fetching additional info for movie {movie_dict.get('title')} from GraphQL")
                imdb_data = await IMDBGraphQLService.get_movie_details(movie_dict["imdb_id"])
                
                # Actualizar la base de datos con la nueva información
                if imdb_data:
                    # Actualizar campos solo si tenemos datos nuevos
                    update_fields = {}
                    
                    if imdb_data.get("director") and len(imdb_data["director"]) > 0:
                        update_fields["director"] = imdb_data["director"]
                        
                    if imdb_data.get("cast") and len(imdb_data["cast"]) > 0:
                        update_fields["casting"] = imdb_data["cast"]
                    
                    if update_fields:
                        # Construir la consulta de actualización dinámicamente
                        set_clauses = ", ".join([f"{key} = ${i+1}" for i, key in enumerate(update_fields.keys())])
                        values = list(update_fields.values())
                        
                        # Añadir el ID como último parámetro
                        query = f"UPDATE movies SET {set_clauses} WHERE id = ${len(values)+1} RETURNING *"
                        values.append(uuid.UUID(movie_id))
                        
                        # Ejecutar la actualización
                        updated_movie = await conn.fetchrow(query, *values)
                        if updated_movie:
                            # Actualizar movie_dict pero mantener la info de visualización
                            view_percentage = movie_dict["view_percentage"]
                            completed = movie_dict["completed"]
                            movie_dict = dict(updated_movie)
                            movie_dict["view_percentage"] = view_percentage
                            movie_dict["completed"] = completed
            
            # Decodificar torrents si están en formato JSON string
            torrents = movie_dict.get("torrents")
            if torrents and isinstance(torrents, str):
                try:
                    movie_dict["torrents"] = json.loads(torrents)
                except:
                    movie_dict["torrents"] = []
            
            # Obtener el torrent hash del primer torrent disponible (si existe)
            torrent_hash = None
            if movie_dict.get("torrents") and isinstance(movie_dict["torrents"], list) and len(movie_dict["torrents"]) > 0:
                torrent_hash = movie_dict["torrents"][0].get("hash")
            
            # Adaptar los campos para el formato de respuesta
            result = {
                "id": str(movie_dict["id"]),
                "imdb_id": movie_dict.get("imdb_id"),
                "title": movie_dict.get("title"),
                "year": movie_dict.get("year"),
                "rating": movie_dict.get("imdb_rating"),
                "runtime": movie_dict.get("duration"),
                "genres": movie_dict.get("genres", []),
                "summary": movie_dict.get("summary", ""),
                "poster": movie_dict.get("cover_image"),
                "director": movie_dict.get("director", []),
                "cast": movie_dict.get("casting", []),
                "torrents": movie_dict.get("torrents", []),
                "torrent_hash": torrent_hash,
                "download_status": movie_dict.get("download_status"),
                "download_progress": movie_dict.get("download_progress", 0),
                # Nuevos campos de visualización
                "view_percentage": movie_dict.get("view_percentage", 0.0),
                "completed": movie_dict.get("completed", False)
            }
            
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting movie details: {str(e)}"
        )

@router.put("/{movie_id}/view", response_model=ViewProgressResponse)
async def update_view_progress(
    movie_id: str,
    progress_data: ViewProgressUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Actualizar el progreso de visualización de una película
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
        user_id = current_user["id"]
        
        async with get_db_connection() as conn:
            # Verificar que la película existe
            movie_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM movies WHERE id = $1)",
                movie_uuid
            )
            
            if not movie_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Movie not found"
                )
            
            # Determinar si está completada (≥90%)
            completed = progress_data.view_percentage >= 90.0
            now = datetime.now()
            
            # Usar UPSERT para actualizar o insertar
            result = await conn.fetchrow(
                """
                INSERT INTO user_movie_views (id, user_id, movie_id, view_percentage, completed, first_viewed_at, last_viewed_at, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $6, $6, $6)
                ON CONFLICT (user_id, movie_id) 
                DO UPDATE SET 
                    view_percentage = GREATEST(user_movie_views.view_percentage, EXCLUDED.view_percentage),
                    completed = (GREATEST(user_movie_views.view_percentage, EXCLUDED.view_percentage) >= 90.0),
                    last_viewed_at = EXCLUDED.last_viewed_at,
                    updated_at = EXCLUDED.updated_at
                RETURNING user_id, movie_id, view_percentage, completed, updated_at
                """,
                uuid.uuid4(), user_id, movie_uuid, progress_data.view_percentage, completed, now
            )
            
            return ViewProgressResponse(
                movie_id=str(result["movie_id"]),
                user_id=str(result["user_id"]),
                view_percentage=result["view_percentage"],
                completed=result["completed"],
                updated_at=result["updated_at"]
            )
            
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid movie ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating view progress: {str(e)}"
        )


@router.post("/{movie_id}/complete", response_model=ViewProgressResponse)
async def mark_movie_complete(
    movie_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Marcar película como completamente vista (100%)
    """
    return await update_view_progress(
        movie_id=movie_id,
        progress_data=ViewProgressUpdate(view_percentage=100.0),
        current_user=current_user
    )


@router.delete("/{movie_id}/view")
async def remove_view_progress(
    movie_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Quitar película de la lista de vistas
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
        user_id = current_user["id"]
        
        async with get_db_connection() as conn:
            deleted = await conn.fetchrow(
                "DELETE FROM user_movie_views WHERE user_id = $1 AND movie_id = $2 RETURNING id",
                user_id, movie_uuid
            )
            
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="View record not found"
                )
            
            return {"message": "View progress removed successfully"}
            
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid movie ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing view progress: {str(e)}"
        )


@router.get("/{movie_id}/view", response_model=Optional[ViewProgressResponse])
async def get_view_progress(
    movie_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener el progreso actual de visualización
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
        user_id = current_user["id"]
        
        async with get_db_connection() as conn:
            progress = await conn.fetchrow(
                """
                SELECT user_id, movie_id, view_percentage, completed, updated_at
                FROM user_movie_views 
                WHERE user_id = $1 AND movie_id = $2
                """,
                user_id, movie_uuid
            )
            
            if not progress:
                return None
            
            return ViewProgressResponse(
                movie_id=str(progress["movie_id"]),
                user_id=str(progress["user_id"]),
                view_percentage=progress["view_percentage"],
                completed=progress["completed"],
                updated_at=progress["updated_at"]
            )
            
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid movie ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting view progress: {str(e)}"
        )


@router.post("/download")
async def download_by_hash(
    request: DownloadRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Descargar película directamente por hash
    """
    try:
        user_id = current_user["id"]
        movie_id = f"direct-{int(time.time())}"
        
        # Preparar mensaje para Kafka
        download_message = {
            'movie_id': movie_id,
            'torrent_hash': request.hash,
            'movie_title': request.title,
            'user_id': str(user_id),
            'timestamp': time.time()
        }
        
        # Enviar a Kafka
        success = kafka_service.send_download_request_enhanced(download_message)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Download service unavailable"
            )
        
        return {
            "message": "Download initiated",
            "movie_id": movie_id,
            "hash": request.hash,
            "title": request.title,
            "status": "downloading"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/{movie_id}/stream")
async def stream_movie(
    movie_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Stream de película (versión básica)
    """
    try:
        # Verificar que la película existe
        async with get_db_connection() as conn:
            movie = await conn.fetchrow(
                "SELECT id, title, file_path FROM movies WHERE id = $1",
                uuid.UUID(movie_id)
            )
            
            if not movie:
                raise HTTPException(404, "Movie not found")
            
            # Por ahora, buscar archivo en /data/movies
            # TODO: Mejorar con información real del torrent service
            movie_files = [
                f"/data/movies/{movie['title']}.mp4",
                f"/data/movies/{movie['title']}.mkv",
                f"/data/movies/{movie_id}.mp4",
                f"/data/movies/{movie_id}.mkv"
            ]
            
            file_path = None
            for path in movie_files:
                if os.path.exists(path):
                    file_path = path
                    break
            
            if not file_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Movie file not available yet. Try downloading first."
                )
            
            # Streaming simple
            async def file_generator():
                async with aiofiles.open(file_path, 'rb') as file:
                    while chunk := await file.read(8192):  # 8KB chunks
                        yield chunk
            
            return StreamingResponse(
                file_generator(),
                media_type="video/mp4",
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Disposition": f"inline; filename={movie['title']}.mp4"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Streaming error: {str(e)}"
        )