# backend/app/api/v1/movies.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import uuid
from app.api.deps import get_current_user
from app.db.session import get_db_connection
from app.models.movie import MovieDetail, MovieSearchResponse
from app.services.imdb_graphql_service import IMDBGraphQLService
import json

router = APIRouter()

@router.get("/{movie_id}", response_model=MovieDetail)
async def get_movie_details(
    movie_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene detalles completos de una película, incluyendo información de APIs externas si es necesario
    """
    try:
        # Buscar la película en la base de datos
        async with get_db_connection() as conn:
            movie = await conn.fetchrow(
                """
                SELECT * FROM movies WHERE id = $1
                """, 
                uuid.UUID(movie_id)
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
                            movie_dict = dict(updated_movie)
            
            # Decodificar torrents si están en formato JSON string
            torrents = movie_dict.get("torrents")
            if torrents and isinstance(torrents, str):
                try:
                    movie_dict["torrents"] = json.loads(torrents)
                except:
                    movie_dict["torrents"] = []
            
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
                "torrent_hash": movie_dict.get("torrent_hash"),
                "download_status": movie_dict.get("download_status"),
                "download_progress": movie_dict.get("download_progress", 0)
            }
            
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting movie details: {str(e)}"
        )