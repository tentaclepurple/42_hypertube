# backend/app/api/v1/user_activity.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
import uuid
import json

from app.api.deps import get_current_user
from app.db.session import get_db_connection
from app.models.user_activity import (
    FavoriteResponse, 
    FavoriteMovieResponse, 
    ContinueWatchingResponse,
    UserActivitySummary
)

router = APIRouter()


@router.post("/favorites/{movie_id}", response_model=FavoriteResponse)
async def add_to_favorites(
    movie_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Add a movie to user's favorites
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
        user_id = current_user["id"]
        
        async with get_db_connection() as conn:
            # Verify that the movie exists
            movie_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM movies WHERE id = $1)",
                movie_uuid
            )
            
            if not movie_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Movie not found"
                )

            # Add to favorites (ignore if already exists due to UNIQUE constraint)
            result = await conn.fetchrow(
                """
                INSERT INTO user_movie_favorites (user_id, movie_id, created_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, movie_id) DO NOTHING
                RETURNING user_id, movie_id, created_at
                """,
                user_id, movie_uuid, datetime.now()
            )
            
            if not result:
                # Already in favorites
                existing = await conn.fetchrow(
                    "SELECT user_id, movie_id, created_at FROM user_movie_favorites WHERE user_id = $1 AND movie_id = $2",
                    user_id, movie_uuid
                )
                result = existing
            
            return FavoriteResponse(
                user_id=str(result["user_id"]),
                movie_id=str(result["movie_id"]),
                created_at=result["created_at"]
            )
            
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid movie ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding to favorites: {str(e)}"
        )


@router.delete("/favorites/{movie_id}")
async def remove_from_favorites(
    movie_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Remove a movie from user's favorites
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
        user_id = current_user["id"]
        
        async with get_db_connection() as conn:
            deleted = await conn.fetchrow(
                "DELETE FROM user_movie_favorites WHERE user_id = $1 AND movie_id = $2 RETURNING id",
                user_id, movie_uuid
            )
            
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Movie not in favorites"
                )
            
            return {"message": "Movie removed from favorites successfully"}
            
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
            detail=f"Error removing from favorites: {str(e)}"
        )


@router.get("/favorites", response_model=List[FavoriteMovieResponse])
async def get_user_favorites(
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get a list of user's favorite movies with viewing information
    """
    try:
        user_id = current_user["id"]
        offset = (page - 1) * limit
        
        async with get_db_connection() as conn:
            favorites = await conn.fetch(
                """
                SELECT 
                    m.id,
                    m.title,
                    m.cover_image as poster,
                    m.year,
                    m.imdb_rating as rating,
                    m.genres,
                    f.created_at,
                    COALESCE(umv.view_percentage, 0.0) as view_percentage,
                    COALESCE(umv.completed, false) as completed
                FROM user_movie_favorites f
                JOIN movies m ON f.movie_id = m.id
                LEFT JOIN user_movie_views umv ON m.id = umv.movie_id AND umv.user_id = f.user_id
                WHERE f.user_id = $1
                ORDER BY f.created_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id, limit, offset
            )
            
            result = []
            for fav in favorites:
                # Decode genres if stored as JSON
                genres = fav["genres"] if fav["genres"] else []
                if isinstance(genres, str):
                    try:
                        genres = json.loads(genres)
                    except:
                        genres = []
                
                result.append(FavoriteMovieResponse(
                    id=str(fav["id"]),
                    title=fav["title"],
                    poster=fav["poster"],
                    year=fav["year"],
                    rating=fav["rating"],
                    genres=genres,
                    created_at=fav["created_at"],
                    view_percentage=fav["view_percentage"],
                    completed=fav["completed"]
                ))
            
            return result
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting favorites: {str(e)}"
        )


@router.get("/continue-watching", response_model=List[ContinueWatchingResponse])
async def get_continue_watching(
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get a list of movies to continue watching (20% <= progress < 90%)
    """
    try:
        user_id = current_user["id"]
        offset = (page - 1) * limit
        
        async with get_db_connection() as conn:
            continue_watching = await conn.fetch(
                """
                SELECT 
                    m.id,
                    m.title,
                    m.cover_image as poster,
                    m.year,
                    m.imdb_rating as rating,
                    m.genres,
                    umv.view_percentage,
                    umv.last_viewed_at
                FROM user_movie_views umv
                JOIN movies m ON umv.movie_id = m.id
                WHERE umv.user_id = $1 
                    AND umv.view_percentage >= 20.0 
                    AND umv.view_percentage < 90.0
                ORDER BY umv.last_viewed_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id, limit, offset
            )
            
            result = []
            for movie in continue_watching:
                # Decodificar géneros si están en formato JSON
                genres = movie["genres"] if movie["genres"] else []
                if isinstance(genres, str):
                    try:
                        genres = json.loads(genres)
                    except:
                        genres = []
                
                result.append(ContinueWatchingResponse(
                    id=str(movie["id"]),
                    title=movie["title"],
                    poster=movie["poster"],
                    year=movie["year"],
                    rating=movie["rating"],
                    genres=genres,
                    view_percentage=movie["view_percentage"],
                    last_viewed_at=movie["last_viewed_at"]
                ))
            
            return result
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting continue watching: {str(e)}"
        )


@router.get("/check-favorite/{movie_id}")
async def check_if_favorite(
    movie_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Check if a movie is in user's favorites
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
        user_id = current_user["id"]
        
        async with get_db_connection() as conn:
            is_favorite = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM user_movie_favorites WHERE user_id = $1 AND movie_id = $2)",
                user_id, movie_uuid
            )
            
            return {"is_favorite": is_favorite}
            
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid movie ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking favorite status: {str(e)}"
        )


@router.get("/summary", response_model=UserActivitySummary)
async def get_user_activity_summary(
    current_user: dict = Depends(get_current_user)
):
    """
    Get a summary of user activity
    """
    try:
        user_id = current_user["id"]
        
        async with get_db_connection() as conn:
            # Count favorites
            favorites_count = await conn.fetchval(
                "SELECT COUNT(*) FROM user_movie_favorites WHERE user_id = $1",
                user_id
            )
            
            # Count continue watching (20% <= progress < 90%)
            continue_watching_count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM user_movie_views 
                WHERE user_id = $1 AND view_percentage >= 20.0 AND view_percentage < 90.0
                """,
                user_id
            )
            
            # Count completed movies
            completed_movies = await conn.fetchval(
                "SELECT COUNT(*) FROM user_movie_views WHERE user_id = $1 AND completed = true",
                user_id
            )
            
            return UserActivitySummary(
                favorites_count=favorites_count or 0,
                continue_watching_count=continue_watching_count or 0,
                completed_movies=completed_movies or 0
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting activity summary: {str(e)}"
        )


@router.get("/recently-watched", response_model=List[ContinueWatchingResponse])
async def get_recently_watched(
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Items per page")
):
    """
    Get a list of recently watched movies (any progress > 0%)
    """
    try:
        user_id = current_user["id"]
        offset = (page - 1) * limit
        
        async with get_db_connection() as conn:
            recently_watched = await conn.fetch(
                """
                SELECT 
                    m.id,
                    m.title,
                    m.cover_image as poster,
                    m.year,
                    m.imdb_rating as rating,
                    m.genres,
                    umv.view_percentage,
                    umv.last_viewed_at
                FROM user_movie_views umv
                JOIN movies m ON umv.movie_id = m.id
                WHERE umv.user_id = $1 AND umv.view_percentage > 0.0
                ORDER BY umv.last_viewed_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id, limit, offset
            )
            
            result = []
            for movie in recently_watched:
                # Decode genres if stored as JSON
                genres = movie["genres"] if movie["genres"] else []
                if isinstance(genres, str):
                    try:
                        genres = json.loads(genres)
                    except:
                        genres = []
                
                result.append(ContinueWatchingResponse(
                    id=str(movie["id"]),
                    title=movie["title"],
                    poster=movie["poster"],
                    year=movie["year"],
                    rating=movie["rating"],
                    genres=genres,
                    view_percentage=movie["view_percentage"],
                    last_viewed_at=movie["last_viewed_at"]
                ))
            
            return result
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recently watched: {str(e)}"
        )


@router.post("/favorites/{movie_id}/toggle")
async def toggle_favorite(
    movie_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Toggle a movie in user's favorites (add if not favorite, remove if favorite)
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
        user_id = current_user["id"]
        
        async with get_db_connection() as conn:
            # Verify that the movie exists
            movie_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM movies WHERE id = $1)",
                movie_uuid
            )
            
            if not movie_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Movie not found"
                )

            # Check if already in favorites
            existing_favorite = await conn.fetchrow(
                "SELECT id, created_at FROM user_movie_favorites WHERE user_id = $1 AND movie_id = $2",
                user_id, movie_uuid
            )
            
            if existing_favorite:
                # Remove from favorites
                await conn.execute(
                    "DELETE FROM user_movie_favorites WHERE user_id = $1 AND movie_id = $2",
                    user_id, movie_uuid
                )
                
                return {
                    "action": "removed",
                    "is_favorite": False,
                    "message": "Movie removed from favorites",
                    "movie_id": movie_id
                }
            else:
                # Add to favorites
                result = await conn.fetchrow(
                    """
                    INSERT INTO user_movie_favorites (user_id, movie_id, created_at)
                    VALUES ($1, $2, $3)
                    RETURNING created_at
                    """,
                    user_id, movie_uuid, datetime.now()
                )
                
                return {
                    "action": "added",
                    "is_favorite": True,
                    "message": "Movie added to favorites",
                    "movie_id": movie_id,
                    "created_at": result["created_at"]
                }
            
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid movie ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error toggling favorite: {str(e)}"
        )