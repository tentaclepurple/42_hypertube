# backend/app/api/v1/search.py

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional
import json
from app.services.search_service import SearchService
from app.api.deps import get_current_user
from app.models.movie import MovieSearchResponse, MovieDetail, MovieBasicResponse, PublicMovieResponse
from app.db.session import get_db_connection

router = APIRouter()


@router.get("/movies", response_model=List[MovieBasicResponse])
async def search_movies(
    query: str = Query("", description="Search term"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=50, description="Results per page"),
    current_user: dict = Depends(get_current_user)
):
    """
    Searches for movies by title or keyword and returns basic information with viewing status
    """
    try:
        user_id = current_user["id"]
        basic_results = await SearchService.search_movies_with_views(query, page, limit, user_id)
        return basic_results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching movies: {str(e)}"
        )


@router.get("/popular", response_model=List[MovieBasicResponse])
async def get_popular_movies(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=50, description="Results per page"),
    current_user: dict = Depends(get_current_user)
):
    """
    Gets the most popular movies with basic information and viewing status
    """
    try:
        user_id = current_user["id"]
        basic_results = await SearchService.get_popular_movies_with_views(page, limit, user_id)
        return basic_results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting popular movies: {str(e)}"
        )

@router.get("/popular_full", response_model=List[MovieSearchResponse])
async def get_popular_movies_full(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=50, description="Results per page"),
    current_user: dict = Depends(get_current_user)
):
    """
    Gets the most popular movies with full information
    """
    try:
        results = await SearchService.get_popular_movies(page, limit)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting popular movies: {str(e)}"
        )


@router.get("/movies_full", response_model=List[MovieSearchResponse])
async def search_movies_full(
    query: str = Query("", description="Search term"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=50, description="Results per page"),
    current_user: dict = Depends(get_current_user)
):
    """
    Searches for movies by title or keyword with full information
    """
    try:
        results = await SearchService.search_movies(query, page, limit)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching movies: {str(e)}"
        )


@router.get("/public/list", response_model=List[PublicMovieResponse])
async def get_public_movies_list(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Movies per page")
):
    """
    Get public list of movies with basic details, sorted by Hypertube rating then IMDb rating
    """
    try:
        offset = (page - 1) * limit
        
        async with get_db_connection() as conn:
            movies = await conn.fetch(
                """
                SELECT 
                    m.id,
                    m.title,
                    m.year,
                    m.imdb_rating,
                    m.cover_image as poster,
                    m.genres,
                    ROUND(AVG(mc.rating), 1) as hypertube_rating
                FROM movies m
                LEFT JOIN movie_comments mc ON m.id = mc.movie_id
                GROUP BY m.id, m.title, m.year, m.imdb_rating, m.cover_image, m.genres
                ORDER BY 
                    hypertube_rating DESC NULLS LAST,
                    m.imdb_rating DESC NULLS LAST
                LIMIT $1 OFFSET $2
                """,
                limit, offset
            )
            
            result = []
            for movie in movies:
                # Process genres if stored as JSON string
                genres = movie["genres"] if movie["genres"] else []
                if isinstance(genres, str):
                    try:
                        genres = json.loads(genres)
                    except:
                        genres = []
                
                result.append(PublicMovieResponse(
                    id=str(movie["id"]),
                    title=movie["title"],
                    year=movie["year"],
                    imdb_rating=movie["imdb_rating"],
                    hypertube_rating=movie["hypertube_rating"],
                    poster=movie["poster"],
                    genres=genres
                ))
            
            return result
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving public movies list: {str(e)}"
        )