# backend/app/services/yts_service.py

import aiohttp
import asyncio
from typing import Dict, List, Optional, Any


class YTSService:
    """Servicio para interactuar con la API de YTS.mx"""
    
    BASE_URL = "https://yts.mx/api/v2"
    
    @staticmethod
    async def search_movies(query: str, limit: int = 20, page: int = 1) -> Dict[str, Any]:
        """
        Busca películas en YTS por título
        """
        url = f"{YTSService.BASE_URL}/list_movies.json"
        params = {
            "query_term": query,
            "limit": limit,
            "page": page,
            "sort_by": "download_count",
            "order_by": "desc"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                print(f"YTS search for '{query}' with URL: {url} and params: {params}")
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"YTS response status: {data.get('status')}")
                        return data.get("data", {})
                    else:
                        error_text = await response.text()
                        print(f"YTS API error: {response.status} - {error_text}")
                        return {"movies": []}
        except Exception as e:
            print(f"Error during YTS API call: {str(e)}")
            return {"movies": []}
    
    @staticmethod
    async def get_movie_details(movie_id: str) -> Dict[str, Any]:
        """
        Obtiene detalles de una película específica por ID
        """
        url = f"{YTSService.BASE_URL}/movie_details.json"
        params = {"movie_id": movie_id}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", {}).get("movie", {})
                    else:
                        error_text = await response.text()
                        print(f"YTS API error: {response.status} - {error_text}")
                        return {}
        except Exception as e:
            print(f"Error during YTS API call: {str(e)}")
            return {}
            
    @staticmethod
    async def get_popular_movies(limit: int = 20, page: int = 1) -> Dict[str, Any]:
        """
        Obtiene las películas más populares de YTS
        """
        url = f"{YTSService.BASE_URL}/list_movies.json"
        params = {
            "limit": limit,
            "page": page,
            "sort_by": "download_count",
            "order_by": "desc"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", {})
                    else:
                        error_text = await response.text()
                        print(f"YTS API error: {response.status} - {error_text}")
                        return {"movies": []}
        except Exception as e:
            print(f"Error during YTS API call: {str(e)}")
            return {"movies": []}