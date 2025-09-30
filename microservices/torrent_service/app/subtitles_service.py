# microservices/torrent_service/app/subtitles_service.py

import aiohttp
import asyncio
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class SubtitlesService:
    """Service to download subtitles from OpenSubtitles API"""
    
    BASE_URL = "https://api.opensubtitles.com/api/v1"
    
    def __init__(self):
        self.api_key = os.environ.get("OP_SUBT_KEY")
        print(f"SUBTITLES: Initializing service with API key: {'YES' if self.api_key else 'NO'}", flush=True)
        if not self.api_key:
            print("SUBTITLES: WARNING - OP_SUBT_KEY not found in environment variables", flush=True)
    
    async def download_subtitles_for_movie(
        self, 
        movie_directory: Path, 
        imdb_id: Optional[str] = None, 
        movie_title: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Download Spanish and English subtitles for a movie
        
        Args:
            movie_directory: Directory where subtitles will be saved
            imdb_id: IMDB ID of the movie (preferred)
            movie_title: Title of the movie (fallback)
            
        Returns:
            Dict with download results for each language
        """
        print(f"SUBTITLES: Starting subtitle download process", flush=True)
        print(f"SUBTITLES: Directory: {movie_directory}", flush=True)
        print(f"SUBTITLES: IMDB ID: {imdb_id}", flush=True)
        print(f"SUBTITLES: Title: {movie_title}", flush=True)
        
        if not self.api_key:
            print("SUBTITLES: ERROR - Cannot download subtitles: API key not configured", flush=True)
            return {"spanish": False, "english": False}
        
        if not imdb_id and not movie_title:
            print("SUBTITLES: ERROR - Neither IMDB ID nor title provided", flush=True)
            return {"spanish": False, "english": False}
        
        # Ensure directory exists
        try:
            movie_directory.mkdir(parents=True, exist_ok=True)
            print(f"SUBTITLES: Directory created/verified: {movie_directory}", flush=True)
        except Exception as e:
            print(f"SUBTITLES: ERROR creating directory: {e}", flush=True)
            return {"spanish": False, "english": False}
        
        results = {}
        
        # Download Spanish subtitles
        print(f"SUBTITLES: === Starting Spanish subtitle search ===", flush=True)
        try:
            spanish_success = await self._download_subtitle_for_language(
                movie_directory, "es", "espanol.srt", imdb_id, movie_title
            )
            results["spanish"] = spanish_success
            print(f"SUBTITLES: Spanish result: {spanish_success}", flush=True)
        except Exception as e:
            print(f"SUBTITLES: ERROR in Spanish download: {e}", flush=True)
            results["spanish"] = False
        
        # Download English subtitles
        print(f"SUBTITLES: === Starting English subtitle search ===", flush=True)
        try:
            english_success = await self._download_subtitle_for_language(
                movie_directory, "en", "english.srt", imdb_id, movie_title
            )
            results["english"] = english_success
            print(f"SUBTITLES: English result: {english_success}", flush=True)
        except Exception as e:
            print(f"SUBTITLES: ERROR in English download: {e}", flush=True)
            results["english"] = False
        
        print(f"SUBTITLES: === FINAL RESULTS ===", flush=True)
        print(f"SUBTITLES: Spanish: {results.get('spanish', False)}", flush=True)
        print(f"SUBTITLES: English: {results.get('english', False)}", flush=True)
        
        return results
    
    async def _download_subtitle_for_language(
        self,
        movie_directory: Path,
        language_code: str,
        filename: str,
        imdb_id: Optional[str] = None,
        movie_title: Optional[str] = None
    ) -> bool:
        """
        Download subtitle for a specific language
        """
        print(f"SUBTITLES: Downloading {language_code} subtitle as {filename}", flush=True)
        
        try:
            # Step 1: Search for subtitles
            print(f"SUBTITLES: Searching for {language_code} subtitles...", flush=True)
            subtitle_info = await self._search_subtitle(language_code, imdb_id, movie_title)
            
            if not subtitle_info:
                print(f"SUBTITLES: No {language_code} subtitles found", flush=True)
                return False
            
            print(f"SUBTITLES: Found subtitle info for {language_code}: {subtitle_info.get('file_id')}", flush=True)
            
            # Step 2: Download the subtitle file
            print(f"SUBTITLES: Downloading {language_code} subtitle file...", flush=True)
            success = await self._download_subtitle_file(
                subtitle_info["file_id"], 
                movie_directory / filename
            )
            
            if success:
                print(f"SUBTITLES: SUCCESS - Downloaded {language_code} subtitle as {filename}", flush=True)
            else:
                print(f"SUBTITLES: FAILED - Could not download {language_code} subtitle", flush=True)
            
            return success
            
        except Exception as e:
            print(f"SUBTITLES: ERROR downloading {language_code} subtitle: {str(e)}", flush=True)
            return False
    
    def _clean_imdb_id(self, imdb_id: str) -> str:
        """Clean IMDB ID format for API compatibility"""
        if not imdb_id:
            return imdb_id
        
        # Remove 'tt' prefix if present
        if imdb_id.startswith('tt'):
            clean_id = imdb_id[2:]  # Remove 'tt' prefix
            print(f"SUBTITLES: Cleaned IMDB ID from {imdb_id} to {clean_id}", flush=True)
            return clean_id
        
        # Remove leading zeros if present
        if imdb_id.startswith('0'):
            clean_id = imdb_id.lstrip('0')
            print(f"SUBTITLES: Removed leading zeros from {imdb_id} to {clean_id}", flush=True)
            return clean_id
        
        return imdb_id
    
    async def _search_subtitle(
        self, 
        language_code: str, 
        imdb_id: Optional[str] = None, 
        movie_title: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Search for a subtitle using IMDB ID or movie title
        """
        print(f"SUBTITLES: Preparing search for {language_code}", flush=True)
        
        headers = {
            'Api-Key': self.api_key,
            'User-Agent': 'Hypertube v1.0',
            'Accept': 'application/json'
        }
        
        # Build search parameters with required fields from working script
        params = {
            'languages': language_code,
            'per_page': 1,  # Integer, not string
            'order_by': 'download_count',  # Required parameter
            'order_direction': 'desc'  # Required parameter
        }
        
        # Prefer IMDB ID search over title search
        if imdb_id:
            clean_imdb_id = self._clean_imdb_id(imdb_id)
            params['imdb_id'] = clean_imdb_id
            search_method = f"IMDB ID {clean_imdb_id}"
        elif movie_title:
            params['query'] = movie_title
            search_method = f"title '{movie_title}'"
        else:
            print(f"SUBTITLES: No search parameters available", flush=True)
            return None
        
        print(f"SUBTITLES: Searching by {search_method} in {language_code}", flush=True)
        print(f"SUBTITLES: API URL: {self.BASE_URL}/subtitles", flush=True)
        print(f"SUBTITLES: Params: {params}", flush=True)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/subtitles",
                    headers=headers,
                    params=params
                ) as response:
                    
                    print(f"SUBTITLES: API response status: {response.status}", flush=True)
                    
                    if response.status != 200:
                        response_text = await response.text()
                        print(f"SUBTITLES: API search failed: {response.status} - {response_text[:200]}", flush=True)
                        return None
                    
                    data = await response.json()
                    print(f"SUBTITLES: API returned data structure: {type(data)}", flush=True)
                    
                    if not data.get("data") or len(data["data"]) == 0:
                        print(f"SUBTITLES: No subtitles found for {search_method}", flush=True)
                        return None
                    
                    print(f"SUBTITLES: Found {len(data['data'])} results", flush=True)
                    
                    # Get the first result
                    first_result = data["data"][0]
                    attributes = first_result.get("attributes", {})
                    files = attributes.get("files", [])
                    
                    print(f"SUBTITLES: First result has {len(files)} files", flush=True)
                    
                    if not files or len(files) == 0:
                        print(f"SUBTITLES: No files available for subtitle", flush=True)
                        return None
                    
                    file_info = files[0]
                    file_id = file_info.get("file_id")
                    
                    print(f"SUBTITLES: File ID extracted: {file_id}", flush=True)
                    
                    if not file_id:
                        print(f"SUBTITLES: No file_id found in subtitle data", flush=True)
                        return None
                    
                    subtitle_info = {
                        "file_id": file_id,
                        "release": attributes.get("release", ""),
                        "download_count": attributes.get("download_count", 0)
                    }
                    
                    print(f"SUBTITLES: Returning subtitle info: {subtitle_info}", flush=True)
                    return subtitle_info
                    
        except Exception as e:
            print(f"SUBTITLES: ERROR searching subtitles: {str(e)}", flush=True)
            return None
    
    async def _download_subtitle_file(self, file_id: int, output_path: Path) -> bool:
        """
        Download subtitle file using the file_id
        """
        print(f"SUBTITLES: Starting file download for file_id: {file_id}", flush=True)
        print(f"SUBTITLES: Output path: {output_path}", flush=True)
        
        headers = {
            'Api-Key': self.api_key,
            'User-Agent': 'Hypertube v1.0',
            'Accept': 'application/json'
        }
        
        data = {
            'file_id': file_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                print(f"SUBTITLES: Making download request to API...", flush=True)
                
                # Step 1: Get download link
                async with session.post(
                    f"{self.BASE_URL}/download",
                    headers=headers,
                    json=data
                ) as response:
                    
                    print(f"SUBTITLES: Download API response status: {response.status}", flush=True)
                    
                    if response.status != 200:
                        response_text = await response.text()
                        print(f"SUBTITLES: Download request failed: {response.status} - {response_text[:200]}", flush=True)
                        return False
                    
                    download_info = await response.json()
                    print(f"SUBTITLES: Download response keys: {list(download_info.keys())}", flush=True)
                    
                    if 'link' not in download_info:
                        print("SUBTITLES: No download link in API response", flush=True)
                        return False
                    
                    download_url = download_info['link']
                    print(f"SUBTITLES: Got download URL: {download_url[:50]}...", flush=True)
                
                # Step 2: Download the actual file
                print(f"SUBTITLES: Downloading file content...", flush=True)
                async with session.get(download_url) as file_response:
                    
                    print(f"SUBTITLES: File download response status: {file_response.status}", flush=True)
                    
                    if file_response.status != 200:
                        print(f"SUBTITLES: File download failed: {file_response.status}", flush=True)
                        return False
                    
                    # Save file to disk
                    content = await file_response.read()
                    print(f"SUBTITLES: Downloaded {len(content)} bytes", flush=True)
                    
                    try:
                        with open(output_path, 'wb') as f:
                            f.write(content)
                        
                        print(f"SUBTITLES: File saved successfully: {output_path.name}", flush=True)
                        return True
                    except Exception as e:
                        print(f"SUBTITLES: ERROR saving file: {e}", flush=True)
                        return False
                    
        except Exception as e:
            print(f"SUBTITLES: ERROR during file download: {str(e)}", flush=True)
            return False