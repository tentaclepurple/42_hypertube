# backend/app/api/v1/movies.py

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Header
from fastapi.responses import StreamingResponse, Response
from typing import List, Optional, Dict
from datetime import datetime
import json
import time
import uuid
import os
import mimetypes
from pathlib import Path
import aiofiles
import logging

from app.api.deps import get_current_user, get_current_user_from_cookie
from app.db.session import get_db_connection
from app.models.movie import MovieDetail, MovieSearchResponse, DownloadRequest
from app.models.view_progress import ViewProgressUpdate, ViewProgressResponse
from app.services.imdb_graphql_service import IMDBGraphQLService
from app.services.kafka_service import kafka_service
from app.services.cleanup_service import cleanup_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{movie_id}", response_model=MovieDetail)
async def get_movie_details(
    movie_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed movie information, including user-specific view progress
    """
    try:
        
        user_id = current_user["id"]

        try:
            cleanup_stats = await cleanup_service.check_and_cleanup_if_needed()
            if cleanup_stats.get("cleanup_executed", False):
                logger.info(f"Clean done: {cleanup_stats}")
        except Exception as e:
            logger.error(f"Cleaning error: {e}")

        
        async with get_db_connection() as conn:
            movie = await conn.fetchrow(
                """
                SELECT 
                    m.*,
                    COALESCE(umv.view_percentage, 0.0) as view_percentage,
                    COALESCE(umv.completed, false) as completed,
                    ROUND(AVG(mc.rating), 1) as hypertube_rating
                FROM movies m
                LEFT JOIN user_movie_views umv ON m.id = umv.movie_id AND umv.user_id = $2
                LEFT JOIN movie_comments mc ON m.id = mc.movie_id
                WHERE m.id = $1
                GROUP BY m.id, umv.view_percentage, umv.completed
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
            
            needs_additional_info = (
                not movie_dict.get("director") or 
                len(movie_dict.get("director", [])) == 0 or
                not movie_dict.get("casting") or
                len(movie_dict.get("casting", [])) == 0
            )
            
            if needs_additional_info and movie_dict.get("imdb_id"):
                print(f"Fetching additional info for movie {movie_dict.get('title')} from GraphQL")
                imdb_data = await IMDBGraphQLService.get_movie_details(movie_dict["imdb_id"])
                
                if imdb_data:
                    update_fields = {}
                    
                    if imdb_data.get("director") and len(imdb_data["director"]) > 0:
                        update_fields["director"] = imdb_data["director"]
                        
                    if imdb_data.get("cast") and len(imdb_data["cast"]) > 0:
                        update_fields["casting"] = imdb_data["cast"]
                    
                    if update_fields:
                        # build dynamic SET clause
                        set_clauses = ", ".join([f"{key} = ${i+1}" for i, key in enumerate(update_fields.keys())])
                        values = list(update_fields.values())
                        
                        # add movie_id as last parameter
                        query = f"UPDATE movies SET {set_clauses} WHERE id = ${len(values)+1} RETURNING *"
                        values.append(uuid.UUID(movie_id))
                        
                        updated_movie = await conn.fetchrow(query, *values)
                        if updated_movie:
                            view_percentage = movie_dict["view_percentage"]
                            completed = movie_dict["completed"]
                            movie_dict = dict(updated_movie)
                            movie_dict["view_percentage"] = view_percentage
                            movie_dict["completed"] = completed
            
            # Decode torrents if stored as JSON string
            torrents = movie_dict.get("torrents")
            if torrents and isinstance(torrents, str):
                try:
                    movie_dict["torrents"] = json.loads(torrents)
                except:
                    movie_dict["torrents"] = []
            
            # Get the first torrent hash if available
            torrent_hash = None
            if movie_dict.get("torrents") and isinstance(movie_dict["torrents"], list) and len(movie_dict["torrents"]) > 0:
                torrent_hash = movie_dict["torrents"][0].get("hash")
            
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
                "view_percentage": movie_dict.get("view_percentage", 0.0),
                "completed": movie_dict.get("completed", False),
                "hypertube_rating": movie_dict.get("hypertube_rating"),
            }
            
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting movie details: {str(e)}"
        )


@router.get("/{movie_id}/stream")
async def stream_movie(
    movie_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user_from_cookie),
    torrent_hash: str = Query(..., description="Specific torrent hash (quality)"),
    range: str = Header(None)
):
    """
    Unified streaming endpoint that:
    1. Checks if movie with specific hash is downloaded
    2. Initiates download if not exists
    3. Streams when sufficient data is available
    4. Handles progressive streaming during download
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
        user_id = current_user["id"]
        
        
        logger.info(f"BACKEND: Stream request for movie {movie_id}, hash {torrent_hash}")
        
        async with get_db_connection() as conn:
            # Check if movie exists in movies table
            movie_info = await conn.fetchrow(
                "SELECT id, title, torrents FROM movies WHERE id = $1",
                movie_uuid
            )
            
            if not movie_info:
                raise HTTPException(404, "Movie not found")
            
            movie_title = movie_info["title"]
            logger.info(f"BACKEND: Movie found: {movie_title}")
            
            # Validate that the hash exists in movie's torrents
            torrents = movie_info["torrents"]
            if isinstance(torrents, str):
                try:
                    torrents = json.loads(torrents)
                except:
                    torrents = []
            
            valid_hash = False
            if torrents and isinstance(torrents, list):
                valid_hash = any(t.get("hash", "").lower() == torrent_hash.lower() 
                               for t in torrents)
            
            if not valid_hash:
                raise HTTPException(400, f"Invalid torrent hash for this movie")
            
            # Check download status for this specific hash
            download_info = await conn.fetchrow(
                """
                SELECT downloaded_lg, filepath_ds, hash_id, update_dt
                FROM movie_downloads_42 
                WHERE movie_id = $1 AND hash_id = $2
                ORDER BY update_dt DESC
                LIMIT 1
                """,
                movie_uuid, torrent_hash.lower()
            )
            
            logger.info(f"BACKEND: Download info query result: {download_info}")
        
        # CASE 1: Already fully downloaded
        if download_info and download_info["downloaded_lg"] and download_info["filepath_ds"]:
            file_path = download_info["filepath_ds"]
            
            if os.path.exists(file_path):
                logger.info(f"BACKEND: Serving fully downloaded file: {file_path}")
                return await _serve_complete_file(file_path, movie_title, range)
            else:
                # File was deleted, mark as not downloaded
                async with get_db_connection() as conn:
                    await conn.execute(
                        "UPDATE movie_downloads_42 SET downloaded_lg = false WHERE hash_id = $1",
                        torrent_hash.lower()
                    )
                logger.warning(f"BACKEND: Downloaded file missing, marked as not downloaded: {file_path}")
        
        # CASE 2: Currently downloading
        if download_info and download_info["filepath_ds"]:
            file_path = download_info["filepath_ds"]
            
            if os.path.exists(file_path):
                can_stream = await _check_streaming_threshold(Path(file_path))
                file_size = Path(file_path).stat().st_size
                
                logger.info(f"BACKEND: Found downloading file: {file_path}, size: {file_size}, can_stream: {can_stream}")
                
                if can_stream:
                    logger.info(f"BACKEND: Serving partial file during download: {file_path}")
                    return await _serve_partial_file(Path(file_path), movie_title, range)
                else:
                    # Not enough data yet, return status
                    logger.info(f"BACKEND: File too small for streaming: {file_size} bytes")
                    raise HTTPException(
                        status_code=202,
                        detail={
                            "message": "Download in progress, please wait",
                            "downloaded_bytes": file_size,
                            "status": "downloading",
                            "estimated_wait": "1-2 minutes"
                        }
                    )
            else:
                logger.warning(f"BACKEND: Filepath in DB but file doesn't exist: {file_path}")
        
        # Check if we found ANY download info but without filepath
        if download_info:
            logger.info(f"BACKEND: Download info found but no valid filepath: {download_info}")
            raise HTTPException(
                status_code=202,
                detail={
                    "message": "Download in progress, file not detected yet",
                    "status": "downloading",
                    "estimated_wait": "30 seconds"
                }
            )
        
        # CASE 3: Not downloaded, need to start download
        logger.info(f"BACKEND: No download found for movie {movie_id}, hash {torrent_hash} - starting new download")
        
        # Initiate download via Kafka
        download_message = {
            'movie_id': str(movie_uuid),
            'torrent_hash': torrent_hash,
            'movie_title': movie_title,
            'user_id': str(user_id),
            'timestamp': time.time(),
            'initiated_by': 'streaming_request'
        }
        
        success = kafka_service.send_download_request_enhanced(download_message)
        
        if not success:
            raise HTTPException(503, "Download service unavailable")
        
        # Return immediate response that download has started
        raise HTTPException(
            status_code=202,  # Accepted, processing
            detail={
                "message": "Download initiated, please wait",
                "status": "starting_download",
                "movie_id": str(movie_uuid),
                "torrent_hash": torrent_hash,
                "estimated_wait": "2-5 minutes",
                "retry_after": 30  # Suggest client retry after 30 seconds
            }
        )
        
    except ValueError:
        raise HTTPException(400, "Invalid movie ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"BACKEND: Streaming error: {str(e)}")
        raise HTTPException(500, f"Streaming error: {str(e)}")


async def _serve_complete_file(file_path: str, movie_title: str, range_header: str = None):
    """Serve a completely downloaded file with range support"""
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        raise HTTPException(404, "Movie file not found on disk")
    
    file_size = file_path_obj.stat().st_size
    content_type = _get_video_content_type(file_path)
    
    # Handle range requests (for video seeking)
    if range_header:
        return await _serve_range_request(file_path, file_size, range_header, content_type, movie_title)
    
    # Serve complete file
    async def file_generator():
        async with aiofiles.open(file_path, 'rb') as file:
            while chunk := await file.read(8192):
                yield chunk
    
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Disposition": f"inline; filename={_sanitize_filename(movie_title)}.mp4"
    }
    
    return StreamingResponse(
        file_generator(),
        media_type=content_type,
        headers=headers
    )


async def _serve_partial_file(file_path: Path, movie_title: str, range_header: str = None):
    """Serve a partially downloaded file"""
    file_size = file_path.stat().st_size
    content_type = _get_video_content_type(str(file_path))
    
    # For partial files, we can only serve from the beginning
    if range_header:
        # Parse range to see if it's asking for the beginning
        try:
            range_match = range_header.replace('bytes=', '').split('-')
            start = int(range_match[0]) if range_match[0] else 0
            
            # If requesting data beyond what we have, return error
            if start >= file_size:
                raise HTTPException(
                    status_code=416,  # Range Not Satisfiable
                    detail="Requested range not available yet"
                )
        except ValueError:
            pass  # Invalid range format, serve from beginning
    
    async def partial_file_generator():
        async with aiofiles.open(file_path, 'rb') as file:
            while chunk := await file.read(8192):
                yield chunk
    
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Disposition": f"inline; filename={_sanitize_filename(movie_title)}.mp4",
        "X-Content-Status": "partial"  # Custom header to indicate partial content
    }
    
    return StreamingResponse(
        partial_file_generator(),
        media_type=content_type,
        headers=headers
    )


async def _serve_range_request(file_path: str, file_size: int, range_header: str, content_type: str, movie_title: str):
    """Handle HTTP range requests for video seeking"""
    try:
        # Parse range header: "bytes=start-end"
        range_match = range_header.replace('bytes=', '').split('-')
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if range_match[1] else file_size - 1
        
        # Validate range
        if start >= file_size or end >= file_size or start > end:
            raise HTTPException(416, "Range Not Satisfiable")
        
        content_length = end - start + 1
        
        async def range_generator():
            async with aiofiles.open(file_path, 'rb') as file:
                await file.seek(start)
                remaining = content_length
                
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
        
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Disposition": f"inline; filename={_sanitize_filename(movie_title)}.mp4"
        }
        
        return StreamingResponse(
            range_generator(),
            status_code=206,  # Partial Content
            media_type=content_type,
            headers=headers
        )
        
    except ValueError:
        raise HTTPException(400, "Invalid range header")


async def _check_streaming_threshold(file_path: Path) -> bool:
    """Check if we have enough REAL data downloaded to start streaming"""
    
    try:
        import os
        import time
        
        stat_info = file_path.stat()
        file_size = stat_info.st_size
        
        blocks_allocated = stat_info.st_blocks * 512
        
        real_downloaded = blocks_allocated
        
        MIN_SIZE_MB = 50
        MIN_PERCENTAGE = 0.25  # At least 25% of actual file size
                
        # Percentage check
        min_percentage_bytes = MIN_PERCENTAGE * file_size
        if real_downloaded >= min_percentage_bytes:
            print(f"DEBUG: Start streaming! - need {min_percentage_bytes/1024/1024:.1f}MB, have {real_downloaded/1024/1024:.1f}MB")
            return True
        
        # # Additional check: if file is actively being written to (modification time is very recent)

        # mtime = stat_info.st_mtime
        # if time.time() - mtime < 60:  # Modified in last minute
        #     if real_downloaded > min_bytes:
        #         print(f"DEBUG: Passed active download check - file recently modified and has {real_downloaded/1024/1024:.1f}MB")
        #         return True

        print(f"DEBUG: Waiting - need {min_percentage_bytes/1024/1024:.1f}MB for 25%, have {real_downloaded/1024/1024:.1f}MB")
        return False
        
    except Exception as e:
        print(f"DEBUG: Error checking real file size: {e}")
        file_size = file_path.stat().st_size
        return file_size > 50 * 1024 * 1024  # Al menos 50MB como fallback


def _get_video_content_type(file_path: str) -> str:
    """Determine MIME type for video file"""
    
    extension = Path(file_path).suffix.lower()
    
    mime_types = {
        '.mp4': 'video/mp4',
        '.mkv': 'video/x-matroska',
        '.avi': 'video/x-msvideo', 
        '.mov': 'video/quicktime',
        '.wmv': 'video/x-ms-wmv',
        '.flv': 'video/x-flv',
        '.webm': 'video/webm',
        '.m4v': 'video/mp4'
    }
    
    return mime_types.get(extension, 'video/mp4')


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename for Content-Disposition header"""
    import re
    # Remove special characters, keep alphanumeric, spaces, hyphens, underscores
    sanitized = re.sub(r'[^\w\s-]', '', filename)
    # Replace spaces with underscores
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized[:100]  # Limit length


@router.get("/{movie_id}/stream/status")
async def get_streaming_status(
    movie_id: str,
    torrent_hash: str = Query(..., description="Specific torrent hash"),
    current_user: dict = Depends(get_current_user)
):
    """
    Check streaming status for specific movie + hash combination
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
        
        async with get_db_connection() as conn:
            download_info = await conn.fetchrow(
                """
                SELECT md.downloaded_lg, md.filepath_ds, md.hash_id, md.update_dt,
                       m.title
                FROM movie_downloads_42 md
                JOIN movies m ON m.id = md.movie_id  
                WHERE md.movie_id = $1 AND md.hash_id = $2
                ORDER BY md.update_dt DESC
                LIMIT 1
                """,
                movie_uuid, torrent_hash.lower()
            )
            
            if not download_info:
                return {
                    "status": "not_started",
                    "message": "Download not initiated",
                    "ready_for_streaming": False,
                    "action_needed": "Call stream endpoint to start download"
                }
            
            # Check if fully downloaded
            if download_info["downloaded_lg"] and download_info["filepath_ds"]:
                if os.path.exists(download_info["filepath_ds"]):
                    file_size = os.path.getsize(download_info["filepath_ds"])
                    return {
                        "status": "ready",
                        "message": "Movie fully downloaded and ready",
                        "ready_for_streaming": True,
                        "file_size": file_size,
                        "download_complete": True,
                        "file_path": download_info["filepath_ds"]
                    }
            
            # Check partial download
            if download_info["filepath_ds"] and os.path.exists(download_info["filepath_ds"]):
                file_path = Path(download_info["filepath_ds"])
                can_stream = await _check_streaming_threshold(file_path)
                file_size = file_path.stat().st_size
                
                # Estimate progress (rough calculation)
                estimated_total = 1.5 * 1024 * 1024 * 1024  # 1.5GB estimate
                progress_percent = min(100, (file_size / estimated_total) * 100)
                
                return {
                    "status": "downloading",
                    "message": "Download in progress",
                    "ready_for_streaming": can_stream,
                    "file_size": file_size,
                    "download_complete": False,
                    "estimated_progress": f"{progress_percent:.1f}%",
                    "file_path": str(file_path),
                    "streaming_available": can_stream
                }
            
            return {
                "status": "starting",
                "message": "Download initiated but file not detected yet",
                "ready_for_streaming": False,
                "retry_in": "30 seconds"
            }
            
    except ValueError:
        raise HTTPException(400, "Invalid movie ID")
    except Exception as e:
        raise HTTPException(500, f"Error checking status: {str(e)}")


@router.get("/{movie_id}/qualities")
async def get_movie_qualities(
    movie_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get available torrent qualities/hashes for a movie
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
        
        async with get_db_connection() as conn:
            movie = await conn.fetchrow(
                "SELECT title, torrents FROM movies WHERE id = $1",
                movie_uuid
            )
            
            if not movie:
                raise HTTPException(404, "Movie not found")
            
            torrents = movie["torrents"]
            if isinstance(torrents, str):
                try:
                    torrents = json.loads(torrents)
                except:
                    torrents = []
            
            if not torrents:
                return {
                    "movie_id": movie_id,
                    "title": movie["title"],
                    "qualities": [],
                    "message": "No torrents available"
                }
            
            # Format torrent info for frontend
            qualities = []
            for torrent in torrents:
                if isinstance(torrent, dict) and torrent.get("hash"):
                    quality_info = {
                        "hash": torrent.get("hash"),
                        "quality": torrent.get("quality", "Unknown"),
                        "size": torrent.get("size", "Unknown"),
                        "seeds": torrent.get("seeds", 0),
                        "peers": torrent.get("peers", 0)
                    }
                    qualities.append(quality_info)
            
            return {
                "movie_id": movie_id,
                "title": movie["title"],
                "qualities": qualities
            }
            
    except ValueError:
        raise HTTPException(400, "Invalid movie ID")
    except Exception as e:
        raise HTTPException(500, f"Error getting qualities: {str(e)}")


@router.put("/{movie_id}/view", response_model=ViewProgressResponse)
async def update_view_progress(
    movie_id: str,
    progress_data: ViewProgressUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update or insert view progress for a movie
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
        user_id = current_user["id"]
        
        async with get_db_connection() as conn:
            # Verify that movie exists
            movie_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM movies WHERE id = $1)",
                movie_uuid
            )
            
            if not movie_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Movie not found"
                )

            # Determine if completed (≥90%)
            completed = progress_data.view_percentage >= 90.0
            now = datetime.now()

            # Use UPSERT to update or insert
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
    Mark movie as completely watched (100%)
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
    Remove movie from view list
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
    Get current view progress
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
    Download movie directly by hash
    """
    try:
        user_id = current_user["id"]
        movie_id = f"direct-{int(time.time())}"
        
        # Prepare message for Kafka
        download_message = {
            'movie_id': movie_id,
            'torrent_hash': request.hash,
            'movie_title': request.title,
            'user_id': str(user_id),
            'timestamp': time.time()
        }

        # Send to Kafka
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


@router.get("/{movie_id}/subtitles")
async def get_movie_subtitles(
    movie_id: str,
    torrent_hash: str = Query(..., description="Specific torrent hash"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all available subtitles for a movie
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
        
        async with get_db_connection() as conn:
            download_info = await conn.fetchrow(
                """
                SELECT filepath_ds FROM movie_downloads_42 
                WHERE movie_id = $1 AND hash_id = $2 AND downloaded_lg = true
                """,
                movie_uuid, torrent_hash.lower()
            )
            
            if not download_info or not download_info["filepath_ds"]:
                return {"subtitles": []}
            
            video_path = Path(download_info["filepath_ds"])
            if not video_path.exists():
                return {"subtitles": []}
                
            movie_dir = video_path.parent
            subtitles = await _find_available_subtitles(movie_dir, movie_id, torrent_hash)
            
            return {"subtitles": subtitles}
            
    except ValueError:
        raise HTTPException(400, "Invalid movie ID format")
    except Exception as e:
        logger.error(f"Error getting subtitles: {str(e)}")
        return {"subtitles": []}


async def _find_available_subtitles(movie_dir: Path, movie_id: str, torrent_hash: str) -> List[Dict]:
    """
    Search for available subtitle files in the movie directory
    """
    subtitles = []
    subtitle_extensions = {'.srt', '.sub', '.vtt', '.ass', '.ssa', '.sbv'}
    
    try:
        for subtitle_file in movie_dir.rglob("*"):
            if subtitle_file.is_file() and subtitle_file.suffix.lower() in subtitle_extensions:
                if subtitle_file.stat().st_size > 0:
                    try:
                        if subtitle_file.stat().st_size == 0:
                            continue

                        relative_path = subtitle_file.relative_to(movie_dir)
                        path_str = str(relative_path)
                        filename_str = str(subtitle_file.name)

                        import re
                        safe_pattern = re.compile(r'^[a-zA-Z0-9._\-/\s()]+$')

                        if not safe_pattern.match(path_str):
                            logger.info(f"Skipping subtitle with special characters in path: {path_str}")
                            continue
                            
                        if not safe_pattern.match(filename_str):
                            logger.info(f"Skipping subtitle with special characters in filename: {filename_str}")
                            continue

                        detected_lang = _detect_subtitle_language(filename_str)
                        
                        subtitles.append({
                            "id": str(uuid.uuid4()),
                            "filename": subtitle_file.name,
                            "language": _detect_subtitle_language(subtitle_file.name),
                            "format": subtitle_file.suffix[1:].upper(),
                            "size": subtitle_file.stat().st_size,
                            "relative_path": str(relative_path),
                            "url": f"{os.environ.get('NEXT_PUBLIC_URL', 'http://localhost:8000')}/api/v1/movies/{movie_id}/subtitles/{relative_path}?torrent_hash={torrent_hash}"
                        })
                    
                    except Exception as e:
                        logger.warning(f"Skipping problematic subtitle file {subtitle_file}: {e}")
                        continue
                        
    except Exception as e:
        logger.error(f"Error scanning subtitles: {e}")
    
    return subtitles


def _detect_subtitle_language(filename: str) -> str:
    """
    Detect subtitle language based on the filename
    """
    
    try:
        filename_lower = filename.lower()
        
        language_patterns = {
            'Spanish': ['spanish', 'español', 'castellano', 'cast', 'spa', 'es'],
            'English': ['english', 'eng', 'en', 'ingles'],
            'French': ['french', 'français', 'francais', 'fra', 'fr'],
            'German': ['german', 'deutsch', 'ger', 'de'],
            'Italian': ['italian', 'italiano', 'ita', 'it'],
            'Portuguese': ['portuguese', 'português', 'portugues', 'por', 'pt'],
            'Japanese': ['japanese', 'jpn', 'ja'],
            'Chinese': ['chinese', 'chi', 'zh'],
            'Korean': ['korean', 'kor', 'ko'],
            'Russian': ['russian', 'rus', 'ru'],
        }
        
        for language, patterns in language_patterns.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    return language
        
        return "Unknown"
        
    except Exception:
        return "Unknown"


@router.get("/{movie_id}/subtitles/{subtitle_path:path}")
async def serve_subtitle_file(
    movie_id: str,
    subtitle_path: str,
    torrent_hash: str = Query(..., description="Torrent hash for verification"),
    current_user: dict = Depends(get_current_user_from_cookie)
):
    """
    Serve specific subtitle file
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
        
        async with get_db_connection() as conn:
            download_info = await conn.fetchrow(
                """
                SELECT filepath_ds FROM movie_downloads_42 
                WHERE movie_id = $1 AND hash_id = $2 AND downloaded_lg = true
                """,
                movie_uuid, torrent_hash.lower()
            )
            
            if not download_info or not download_info["filepath_ds"]:
                raise HTTPException(404, "Movie not found or not downloaded")
            
            video_path = Path(download_info["filepath_ds"])
            movie_dir = video_path.parent
            subtitle_full_path = movie_dir / subtitle_path

            # safeguards
            if not subtitle_full_path.exists():
                raise HTTPException(404, "Subtitle file not found")
            
            if not subtitle_full_path.is_file():
                raise HTTPException(400, "Invalid file path")

            # Verify that the file is within the allowed directory
            try:
                subtitle_full_path.resolve().relative_to(movie_dir.resolve())
            except ValueError:
                raise HTTPException(403, "Access to subtitle file denied")

            # Verify valid extension
            valid_extensions = {'.srt', '.sub', '.vtt', '.ass', '.ssa', '.sbv'}
            if subtitle_full_path.suffix.lower() not in valid_extensions:
                raise HTTPException(400, "Invalid subtitle file format")

            # Determine content type
            content_type = _get_subtitle_content_type(subtitle_full_path.suffix)

            # Serve the file
            async def subtitle_generator():
                async with aiofiles.open(subtitle_full_path, 'rb') as file:
                    while chunk := await file.read(8192):
                        yield chunk
            
            file_size = subtitle_full_path.stat().st_size
            headers = {
                "Content-Length": str(file_size),
                "Content-Disposition": f"inline; filename={subtitle_full_path.name}",
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Credentials": "true",
                "Cache-Control": "public, max-age=3600"
            }
            
            return StreamingResponse(
                subtitle_generator(),
                media_type=content_type,
                headers=headers
            )
            
    except ValueError:
        raise HTTPException(400, "Invalid movie ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving subtitle: {str(e)}")
        raise HTTPException(500, f"Error serving subtitle file")

@router.options("/{movie_id}/subtitles/{subtitle_path:path}")
async def subtitle_options(
    movie_id: str,
    subtitle_path: str,
    torrent_hash: str = Query(..., description="Torrent hash for verification")
):
    """Handle preflight OPTIONS request for subtitles"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400"
        }
    )


def _get_subtitle_content_type(file_extension: str) -> str:
    """
    Determine MIME type for subtitle files
    """
    extension = file_extension.lower()
    
    mime_types = {
        '.srt': 'text/srt',
        '.vtt': 'text/vtt',
        '.sub': 'text/plain',
        '.ass': 'text/x-ssa',
        '.ssa': 'text/x-ssa',
        '.sbv': 'text/plain'
    }
    
    return mime_types.get(extension, 'text/plain')