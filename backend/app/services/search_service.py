# backend/app/services/search_service.py

from typing import Dict, List, Optional, Any
import uuid
import json
from datetime import datetime
from app.services.yts_service import YTSService
from app.db.session import get_db_connection
from .queries import get_popular, insert_movie

class SearchService:
    """Servicio para buscar películas combinando múltiples fuentes"""
    
    @staticmethod
    async def search_movies(query: str, page: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Busca películas en YTS y en la base de datos local con paginación
        """
        print(f"Query: {query}")
        
        # Calcular el offset para la paginación
        offset = (page - 1) * limit
        
        # Buscar primero en la base de datos
        db_results = await SearchService._search_in_database(query, limit, offset)
        print(f"DB results found: {len(db_results)}")
        
        if db_results and len(db_results) >= limit:
            # Si encontramos suficientes resultados en la base de datos, los devolvemos
            return db_results
        
        # Si no hay suficientes resultados en la base de datos o estamos en la primera página, 
        # buscamos en YTS para complementar
        if page == 1 or len(db_results) < limit:
            yts_results = await YTSService.search_movies(query, limit - len(db_results), page)
            yts_movies = yts_results.get("movies", [])
            print(f"YTS movies found: {len(yts_movies)}")
            
            if yts_movies:
                # Transformar y guardar resultados
                transformed_results = await SearchService._transform_yts_results(yts_movies)
                print(f"Transformed results: {len(transformed_results)}")
                
                # Guardar resultados en la base de datos para futuras consultas
                await SearchService._save_to_database(transformed_results)
                
                # Si ya tenemos algunos resultados de la base de datos, completamos hasta el límite
                if db_results:
                    # Filtrar películas de YTS que no estén ya en los resultados de BD
                    db_imdb_ids = {movie.get("imdb_id") for movie in db_results if movie.get("imdb_id")}
                    filtered_yts_results = [
                        movie for movie in transformed_results 
                        if movie.get("imdb_id") not in db_imdb_ids
                    ]
                    
                    # Combinar resultados hasta el límite
                    combined_results = db_results + filtered_yts_results[:limit - len(db_results)]
                    return combined_results
                
                return transformed_results
        
        # Si estamos en una página diferente a la 1 y no hay suficientes resultados,
        # simplemente devolvemos lo que encontramos en la base de datos
        return db_results
    
    @staticmethod
    async def get_popular_movies(page: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obtiene las películas más populares con paginación
        """
        # Calcular el offset basado en la página
        offset = (page - 1) * limit
        
        # Intentar obtener de la base de datos primero
        db_results = await SearchService._get_popular_from_database(limit, offset)
        print(f"DB popular results found: {len(db_results)}")
        
        if db_results and len(db_results) >= limit:
            return db_results[:limit]
        
        # Si no hay suficientes, obtener de YTS
        yts_results = await YTSService.get_popular_movies(limit, page)
        yts_movies = yts_results.get("movies", [])
        print(f"YTS popular movies found: {len(yts_movies)}")
        
        # Transformar y guardar resultados
        transformed_results = await SearchService._transform_yts_results(yts_movies)
        await SearchService._save_to_database(transformed_results)
        
        return transformed_results

    @staticmethod
    async def _transform_yts_results(yts_movies: List[Dict]) -> List[Dict]:
        """
        Transforma los resultados de YTS al formato interno
        """
        results = []
        
        for movie in yts_movies:
            # Solo procesar películas que tienen torrents
            if not movie.get("torrents"):
                continue
                
            # Generar un ID único para la película
            movie_id = str(uuid.uuid4())
            
            # Extraer los datos relevantes
            transformed = {
                "id": movie_id,
                "imdb_id": movie.get("imdb_code"),
                "title": movie.get("title", ""),
                "year": movie.get("year"),
                "rating": movie.get("rating"),
                "runtime": movie.get("runtime"),
                "genres": movie.get("genres", []),
                "summary": movie.get("summary", ""),
                "poster": movie.get("large_cover_image", ""),
                "torrents": movie.get("torrents", []),
                "source": "yts"
            }
            
            results.append(transformed)
            
        return results
    
    @staticmethod
    async def _search_in_database(query: str, limit: int, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Busca películas en la base de datos usando palabras clave múltiples
        """
        # Dividir la consulta en palabras individuales
        words = query.split()
        if not words:
            return []
        
        # Construir una condición que exige todas las palabras
        conditions = []
        params = [limit, offset]  # El límite y offset serán los primeros parámetros
        
        for word in words:
            # Agregar cada palabra como %palabra%
            pattern = f"%{word}%"
            # Buscar en título o resumen
            conditions.append("(title ILIKE $" + str(len(params) + 1) + 
                            " OR title_lower ILIKE $" + str(len(params) + 1) +
                            " OR summary ILIKE $" + str(len(params) + 1) + ")")
            params.append(pattern)
        
        # Construir la consulta SQL completa con paginación
        sql = f"""
            SELECT 
                id, imdb_id, title, year, imdb_rating, genres, summary,
                cover_image, director, casting, torrents
            FROM movies
            WHERE {" AND ".join(conditions)}
            ORDER BY imdb_rating DESC NULLS LAST
            LIMIT $1 OFFSET $2
        """
        
        try:
            async with get_db_connection() as conn:
                results = await conn.fetch(sql, *params)
                
                # Adaptar los resultados
                movies_list = []
                for row in results:
                    movie_dict = dict(row)
                    # Renombrar campos para mantener consistencia
                    movie_dict["id"] = str(movie_dict["id"])
                    movie_dict["poster"] = movie_dict.pop("cover_image")
                    movie_dict["rating"] = movie_dict.pop("imdb_rating")
                    movie_dict["runtime"] = movie_dict.get("duration")
                    movie_dict["source"] = "database"
                    
                    # Decodificar torrents si están en formato JSON string
                    torrents = movie_dict.get("torrents")
                    if torrents and isinstance(torrents, str):
                        try:
                            movie_dict["torrents"] = json.loads(torrents)
                        except Exception as e:
                            print(f"Error parsing torrents JSON for movie {movie_dict['id']}: {str(e)}")
                            movie_dict["torrents"] = []
                    elif torrents is None:
                        movie_dict["torrents"] = []
                    
                    movies_list.append(movie_dict)
                
                return movies_list
        except Exception as e:
            print(f"Error searching in database: {str(e)}")
            return []
    
    @staticmethod
    async def _get_popular_from_database(limit: int, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Obtiene películas populares de la base de datos con paginación
        """
        try:
            async with get_db_connection() as conn:
                results = await conn.fetch(
                    get_popular, 
                    limit, offset
                )
                
                # Adaptar los resultados
                movies_list = []
                for row in results:
                    movie_dict = dict(row)
                    # Renombrar campos para mantener consistencia
                    movie_dict["id"] = str(movie_dict["id"])
                    movie_dict["poster"] = movie_dict.pop("cover_image")
                    movie_dict["rating"] = movie_dict.pop("imdb_rating")
                    movie_dict["runtime"] = movie_dict.get("duration")
                    movie_dict["source"] = "database"
                    
                    # Decodificar torrents si están en formato JSON string
                    torrents = movie_dict.get("torrents")
                    if torrents and isinstance(torrents, str):
                        try:
                            movie_dict["torrents"] = json.loads(torrents)
                        except:
                            movie_dict["torrents"] = []
                    
                    # Extraer el torrent_hash del primer torrent disponible (si existe)
                    if movie_dict.get("torrents") and isinstance(movie_dict["torrents"], list) and len(movie_dict["torrents"]) > 0:
                        movie_dict["torrent_hash"] = movie_dict["torrents"][0].get("hash")
                    else:
                        movie_dict["torrent_hash"] = None
                    
                    movies_list.append(movie_dict)
                
                return movies_list
        except Exception as e:
            print(f"Error getting popular movies from database: {str(e)}")
            return []
    
    @staticmethod
    async def _save_to_database(movies: List[Dict]) -> None:
        """
        Guarda las películas que tienen torrents disponibles
        """
        async with get_db_connection() as conn:
            for movie in movies:
                # Solo procesar películas con torrents disponibles
                if not movie.get("torrents"):
                    continue
                    
                # Comprobar si la película ya existe
                exists = False
                if movie.get("imdb_id"):
                    exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM movies WHERE imdb_id = $1)",
                        movie.get("imdb_id")
                    )
                
                # Si no existe, la insertamos
                if not exists:
                    try:
                        # Insertar la película
                        await conn.execute(
                            insert_movie,
                            uuid.UUID(movie["id"]) if isinstance(movie["id"], str) else movie["id"],
                            movie.get("imdb_id"),
                            movie.get("title", ""),
                            movie.get("title", "").lower(),
                            movie.get("year"),
                            movie.get("rating"),
                            movie.get("genres", []),
                            movie.get("summary", ""),
                            movie.get("poster", ""),
                            movie.get("director", []),
                            movie.get("cast", []),
                            json.dumps(movie.get("torrents", [])),
                            datetime.now()
                        )
                        print(f"Saved movie: {movie.get('title')}")
                    except Exception as e:
                        print(f"Error saving movie {movie.get('title')}: {str(e)}")