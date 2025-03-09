# backend/app/services/imdb_graphql_service.py

import aiohttp
import json
from typing import Dict, List, Any, Optional

class IMDBGraphQLService:
    """Servicio para obtener información adicional de películas vía GraphQL"""
    
    GRAPHQL_URL = "https://graph.imdbapi.dev/v1"
    
    @staticmethod
    async def get_movie_details(imdb_id: str) -> Dict[str, Any]:
        """
        Obtiene detalles adicionales de una película mediante GraphQL
        """
        if not imdb_id:
            print("No IMDB ID provided")
            return {}
            
        # Construir la consulta GraphQL
        query = """
        {
          title(id: "%s") {
            id
            primary_title
         
            # Get the first 5 directors
            directors: credits(first: 5, categories:[ "director" ]) {
              name {
                display_name
                avatars {
                  url
                }
              }
            }
          
            # Get the first 5 casts
            casts: credits(first: 5, categories:[ "actor", "actress" ]) {
              name {
                display_name
                avatars {
                  url
                }
              }
            }
          }
        }
        """ % imdb_id
        
        # Realizar la petición
        try:
            async with aiohttp.ClientSession() as session:
                print(f"Requesting GraphQL data for IMDB ID: {imdb_id}")
                async with session.post(
                    IMDBGraphQLService.GRAPHQL_URL,
                    json={"query": query}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        processed_data = await IMDBGraphQLService._process_graphql_data(result)
                        print(f"GraphQL data processed: {len(processed_data)} fields")
                        return processed_data
                    else:
                        error_text = await response.text()
                        print(f"Error from GraphQL API: {response.status} - {error_text}")
                        return {}
        except Exception as e:
            print(f"Error during GraphQL API call: {str(e)}")
            return {}
    
    @staticmethod
    async def _process_graphql_data(result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa la respuesta de GraphQL para extraer los datos relevantes
        """
        if not result.get("data") or not result["data"].get("title"):
            print("No valid data in GraphQL response")
            return {}
            
        title_data = result["data"]["title"]
        
        # Extraer directores
        directors = []
        for director in title_data.get("directors", []):
            if director.get("name") and director["name"].get("display_name"):
                directors.append(director["name"]["display_name"])
        
        # Extraer cast
        cast = []
        for actor in title_data.get("casts", []):
            if actor.get("name") and actor["name"].get("display_name"):
                cast.append(actor["name"]["display_name"])
        
        return {
            "imdb_id": title_data.get("id"),
            "title": title_data.get("primary_title"),
            "director": directors,
            "cast": cast
        }
