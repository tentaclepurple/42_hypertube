# backend/app/services/search_service.py

from typing import Dict, List, Optional, Any
import uuid
import json
from datetime import datetime
from app.services.yts_service import YTSService
from app.db.session import get_db_connection
from .queries import get_popular, insert_movie

class SearchService:
    """Service for searching and retrieving movies"""
    
    @staticmethod
    async def search_movies_with_views(query: str, page: int = 1, limit: int = 20, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Search for movies with user view information
        """
        print(f"Query: {query}")

        # Calculate the offset for pagination
        offset = (page - 1) * limit

        # Search in the database with view information
        db_results = await SearchService._search_in_database_with_views(query, limit, offset, user_id)
        print(f"DB results found: {len(db_results)}")
        
        if db_results and len(db_results) >= limit:
            return db_results

        # If not enough results, search in YTS and complete
        if page == 1 or len(db_results) < limit:
            yts_results = await YTSService.search_movies(query, limit - len(db_results), page)
            yts_movies = yts_results.get("movies", [])
            print(f"YTS movies found: {len(yts_movies)}")
            
            if yts_movies:
                # Transform and save results
                transformed_results = await SearchService._transform_yts_results(yts_movies)
                await SearchService._save_to_database(transformed_results)

                # Add view information and ensure genres
                for movie in transformed_results:
                    movie["view_percentage"] = 0.0
                    movie["completed"] = False
                    # Ensure genres is present
                    if "genres" not in movie:
                        movie["genres"] = []
                
                if db_results:
                    db_imdb_ids = {movie.get("imdb_id") for movie in db_results if movie.get("imdb_id")}
                    filtered_yts_results = [
                        movie for movie in transformed_results 
                        if movie.get("imdb_id") not in db_imdb_ids
                    ]
                    combined_results = db_results + filtered_yts_results[:limit - len(db_results)]
                    return combined_results
                
                return transformed_results
        
        return db_results
    
    @staticmethod
    async def get_popular_movies_with_views(page: int = 1, limit: int = 20, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get popular movies with view information
        """
        offset = (page - 1) * limit

        # Try to get from the database with view information
        db_results = await SearchService._get_popular_from_database_with_views(limit, offset, user_id)
        print(f"DB popular results found: {len(db_results)}")
        
        if db_results and len(db_results) >= limit:
            return db_results[:limit]

        # If not enough, get from YTS
        yts_results = await YTSService.get_popular_movies(limit, page)
        yts_movies = yts_results.get("movies", [])
        print(f"YTS popular movies found: {len(yts_movies)}")

        # Transform and save results
        transformed_results = await SearchService._transform_yts_results(yts_movies)
        await SearchService._save_to_database(transformed_results)

        # Add view information and ensure genres
        for movie in transformed_results:
            movie["view_percentage"] = 0.0
            movie["completed"] = False
            # Ensure genres is present
            if "genres" not in movie:
                movie["genres"] = []
        
        return transformed_results

    @staticmethod
    async def search_movies(query: str, page: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for movies without view information (for _full endpoints)
        """
        offset = (page - 1) * limit
        db_results = await SearchService._search_in_database(query, limit, offset)
        
        if db_results and len(db_results) >= limit:
            return db_results
        
        if page == 1 or len(db_results) < limit:
            yts_results = await YTSService.search_movies(query, limit - len(db_results), page)
            yts_movies = yts_results.get("movies", [])
            
            if yts_movies:
                transformed_results = await SearchService._transform_yts_results(yts_movies)
                await SearchService._save_to_database(transformed_results)
                
                if db_results:
                    db_imdb_ids = {movie.get("imdb_id") for movie in db_results if movie.get("imdb_id")}
                    filtered_yts_results = [
                        movie for movie in transformed_results 
                        if movie.get("imdb_id") not in db_imdb_ids
                    ]
                    combined_results = db_results + filtered_yts_results[:limit - len(db_results)]
                    return combined_results
                
                return transformed_results
        
        return db_results
    
    @staticmethod
    async def get_popular_movies(page: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get popular movies without view information (for _full endpoints)
        """
        offset = (page - 1) * limit
        db_results = await SearchService._get_popular_from_database(limit, offset)
        
        if db_results and len(db_results) >= limit:
            return db_results[:limit]
        
        yts_results = await YTSService.get_popular_movies(limit, page)
        yts_movies = yts_results.get("movies", [])
        
        transformed_results = await SearchService._transform_yts_results(yts_movies)
        await SearchService._save_to_database(transformed_results)
        
        return transformed_results

    @staticmethod
    async def _search_in_database_with_views(query: str, limit: int, offset: int = 0, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Search for movies in the database with view information
        """
        words = query.split()
        if not words:
            return []
        
        conditions = []
        params = [user_id, limit, offset]  # user_id, limit, and offset as first parameters

        for word in words:
            pattern = f"%{word}%"
            conditions.append("(m.title ILIKE $" + str(len(params) + 1) + 
                            " OR m.title_lower ILIKE $" + str(len(params) + 1) +
                            " OR m.summary ILIKE $" + str(len(params) + 1) + ")")
            params.append(pattern)
        
        sql = f"""
            SELECT 
                m.id, m.imdb_id, m.title, m.year, m.imdb_rating, m.genres,
                m.cover_image,
                COALESCE(umv.view_percentage, 0.0) as view_percentage,
                COALESCE(umv.completed, false) as completed
            FROM movies m
            LEFT JOIN user_movie_views umv ON m.id = umv.movie_id AND umv.user_id = $1
            WHERE {" AND ".join(conditions)}
            ORDER BY m.imdb_rating DESC NULLS LAST
            LIMIT $2 OFFSET $3
        """
        
        try:
            async with get_db_connection() as conn:
                results = await conn.fetch(sql, *params)
                
                movies_list = []
                for row in results:
                    movie_dict = dict(row)
                    movie_dict["id"] = str(movie_dict["id"])
                    movie_dict["poster"] = movie_dict.pop("cover_image")
                    movie_dict["rating"] = movie_dict.pop("imdb_rating")

                    # Ensure genres is a list
                    genres = movie_dict.get("genres", [])
                    if genres is None:
                        movie_dict["genres"] = []
                    elif isinstance(genres, str):
                        # If for some reason it's a string, try to parse it
                        try:
                            movie_dict["genres"] = json.loads(genres)
                        except:
                            movie_dict["genres"] = []
                    else:
                        movie_dict["genres"] = genres
                    
                    movies_list.append(movie_dict)
                
                return movies_list
        except Exception as e:
            print(f"Error searching in database with views: {str(e)}")
            return []

    @staticmethod
    async def _get_popular_from_database_with_views(limit: int, offset: int = 0, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get popular movies with view information and hypertube rating
        """
        sql = """
            SELECT 
                m.id, m.imdb_id, m.title, m.year, m.imdb_rating, m.genres,
                m.cover_image,
                COALESCE(umv.view_percentage, 0.0) as view_percentage,
                COALESCE(umv.completed, false) as completed,
                ROUND(AVG(mc.rating), 1) as hypertube_rating
            FROM movies m
            LEFT JOIN user_movie_views umv ON m.id = umv.movie_id AND umv.user_id = $1
            LEFT JOIN movie_comments mc ON m.id = mc.movie_id
            WHERE m.imdb_rating IS NOT NULL
            GROUP BY m.id, m.imdb_id, m.title, m.year, m.imdb_rating, m.genres, 
                     m.cover_image, umv.view_percentage, umv.completed
            ORDER BY 
                m.imdb_rating DESC NULLS LAST
            LIMIT $2 OFFSET $3
        """
        
        try:
            async with get_db_connection() as conn:
                results = await conn.fetch(sql, user_id, limit, offset)
                
                movies_list = []
                for row in results:
                    movie_dict = dict(row)
                    movie_dict["id"] = str(movie_dict["id"])
                    movie_dict["poster"] = movie_dict.pop("cover_image")
                    movie_dict["rating"] = movie_dict.pop("imdb_rating")
                    
                    genres = movie_dict.get("genres", [])
                    if genres is None:
                        movie_dict["genres"] = []
                    elif isinstance(genres, str):
                        try:
                            movie_dict["genres"] = json.loads(genres)
                        except:
                            movie_dict["genres"] = []
                    else:
                        movie_dict["genres"] = genres
                    
                    movies_list.append(movie_dict)
                
                return movies_list
        except Exception as e:
            print(f"Error getting popular movies from database with views: {str(e)}")
            return []

    @staticmethod
    async def _transform_yts_results(yts_movies: List[Dict]) -> List[Dict]:
        """
        Transform YTS results to internal format
        """
        results = []
        
        for movie in yts_movies:
            if not movie.get("torrents"):
                continue
                
            movie_id = str(uuid.uuid4())
            
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
        Search for movies in the database without view information
        """
        words = query.split()
        if not words:
            return []
        
        conditions = []
        params = [limit, offset]
        
        for word in words:
            pattern = f"%{word}%"
            conditions.append("(title ILIKE $" + str(len(params) + 1) + 
                            " OR title_lower ILIKE $" + str(len(params) + 1) +
                            " OR summary ILIKE $" + str(len(params) + 1) + ")")
            params.append(pattern)
        
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
                
                movies_list = []
                for row in results:
                    movie_dict = dict(row)
                    movie_dict["id"] = str(movie_dict["id"])
                    movie_dict["poster"] = movie_dict.pop("cover_image")
                    movie_dict["rating"] = movie_dict.pop("imdb_rating")
                    movie_dict["runtime"] = movie_dict.get("duration")
                    movie_dict["source"] = "database"
                    
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
        Get popular movies without view information
        """
        try:
            async with get_db_connection() as conn:
                results = await conn.fetch(
                    get_popular, 
                    limit, offset
                )
                
                movies_list = []
                for row in results:
                    movie_dict = dict(row)
                    movie_dict["id"] = str(movie_dict["id"])
                    movie_dict["poster"] = movie_dict.pop("cover_image")
                    movie_dict["rating"] = movie_dict.pop("imdb_rating")
                    movie_dict["runtime"] = movie_dict.get("duration")
                    movie_dict["source"] = "database"
                    
                    torrents = movie_dict.get("torrents")
                    if torrents and isinstance(torrents, str):
                        try:
                            movie_dict["torrents"] = json.loads(torrents)
                        except:
                            movie_dict["torrents"] = []
                    
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
        Save movies that have available torrents
        """
        async with get_db_connection() as conn:
            for movie in movies:
                if not movie.get("torrents"):
                    continue
                    
                exists = False
                if movie.get("imdb_id"):
                    exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM movies WHERE imdb_id = $1)",
                        movie.get("imdb_id")
                    )
                
                if not exists:
                    try:
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
                        