# backend/app/services/imdb_graphql_service.py

import aiohttp
import json
from typing import Dict, List, Any, Optional


class IMDBGraphQLService:
    """Servicio para obtener información adicional de películas vía REST API"""
    
    BASE_URL = "https://api.imdbapi.dev"
    
    @staticmethod
    async def get_movie_details(imdb_id: str) -> Dict[str, Any]:
        """
        Obtiene detalles adicionales de una película mediante REST API
        """
        if not imdb_id:
            print("No IMDB ID provided")
            return {}
            
        # Construir la URL para obtener créditos (directores y actores)
        url = f"{IMDBGraphQLService.BASE_URL}/titles/{imdb_id}/credits"
        params = {
            "categories": ["director", "actor"]
        }
        
        # Realizar la petición
        try:
            async with aiohttp.ClientSession() as session:
                print(f"Requesting REST API data for IMDB ID: {imdb_id}")
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        processed_data = await IMDBGraphQLService._process_api_data(result)
                        print(f"API data processed: {len(processed_data)} fields")
                        return processed_data
                    else:
                        error_text = await response.text()
                        print(f"Error from REST API: {response.status} - {error_text}")
                        return {}
        except Exception as e:
            print(f"Error during REST API call: {str(e)}")
            return {}
    
    @staticmethod
    async def _process_api_data(result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa la respuesta de la REST API para extraer los datos relevantes
        """
        if not result.get("credits"):
            print("No valid credits data in API response")
            return {}
            
        credits = result["credits"]
        
        # Extraer directores
        directors = []
        for credit in credits:
            if credit.get("category") == "director" and credit.get("name", {}).get("displayName"):
                directors.append(credit["name"]["displayName"])
        
        # Extraer cast (actores)
        cast = []
        for credit in credits:
            if credit.get("category") == "actor" and credit.get("name", {}).get("displayName"):
                cast.append(credit["name"]["displayName"])
        
        return {
            "director": directors,
            "cast": cast
        }