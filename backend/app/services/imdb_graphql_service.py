# backend/app/services/imdb_graphql_service.py

import aiohttp
import json
from typing import Dict, List, Any, Optional


class IMDBGraphQLService:
    """Service to interact with IMDB GraphQL and REST APIs"""
    
    BASE_URL = "https://api.imdbapi.dev"
    
    @staticmethod
    async def get_movie_details(imdb_id: str) -> Dict[str, Any]:
        """
        Get movie details including directors and cast from IMDB using REST API
        """
        if not imdb_id:
            print("No IMDB ID provided")
            return {}

        # Build the URL to get credits (directors and actors)
        url = f"{IMDBGraphQLService.BASE_URL}/titles/{imdb_id}/credits"
        params = {
            "categories": ["director", "actor"]
        }

        # Make the request
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
        Process the REST API response to extract relevant data
        """
        if not result.get("credits"):
            print("No valid credits data in API response")
            return {}
            
        credits = result["credits"]

        # Extract directors
        directors = []
        for credit in credits:
            if credit.get("category") == "director" and credit.get("name", {}).get("displayName"):
                directors.append(credit["name"]["displayName"])

        # Extract cast (actors)
        cast = []
        for credit in credits:
            if credit.get("category") == "actor" and credit.get("name", {}).get("displayName"):
                cast.append(credit["name"]["displayName"])
        
        return {
            "director": directors,
            "cast": cast
        }