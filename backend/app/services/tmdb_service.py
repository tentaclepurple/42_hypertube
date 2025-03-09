# backend/app/services/tmdb_service.py
import os
import aiohttp
from typing import Dict, List, Optional, Any


class TMDBService:
    """Servicio para interactuar con la API de TMDB"""
    
    BASE_URL = "https://api.themoviedb.org/3"
    API_KEY = os.environ.get("TMDB_API_KEY")
    
    @staticmethod
    async def search_movies(query: str, page: int = 1) -> Dict[str, Any]:
        """
        Busca películas en TMDB por título
        """
        if not TMDBService.API_KEY:
            raise ValueError("TMDB_API_KEY is not set in environment variables")
            
        url = f"{TMDBService.BASE_URL}/search/movie"
        headers = {"Authorization": f"Bearer {TMDBService.API_KEY}"}
        params = {
            "query": query,
            "page": page,
            "include_adult": "false"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return {"results": []}
    
    @staticmethod
    async def get_movie_details(tmdb_id: int) -> Dict[str, Any]:
        """
        Obtiene detalles de una película por su ID de TMDB
        """
        if not TMDBService.API_KEY:
            raise ValueError("TMDB_API_KEY is not set in environment variables")
            
        url = f"{TMDBService.BASE_URL}/movie/{tmdb_id}"
        params = {
            "api_key": TMDBService.API_KEY,
            "append_to_response": "credits,videos,images"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return {}