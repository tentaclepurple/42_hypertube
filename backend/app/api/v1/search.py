# backend/app/api/v1/search.py

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional
from app.services.search_service import SearchService
from app.api.deps import get_current_user
from app.models.movie import MovieSearchResponse, MovieDetail

router = APIRouter()

@router.get("/movies", response_model=List[MovieSearchResponse])
async def search_movies(
    query: str = Query("", description="Término de búsqueda"),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(20, ge=1, le=50, description="Resultados por página"),
    current_user: dict = Depends(get_current_user)
):
    """
    Busca películas por título o palabra clave
    """
    try:
        results = await SearchService.search_movies(query, page, limit)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching movies: {str(e)}"
        )

@router.get("/popular", response_model=List[MovieSearchResponse])
async def get_popular_movies(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(20, ge=1, le=50, description="Resultados por página"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene las películas más populares
    """
    try:
        results = await SearchService.get_popular_movies(page, limit)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting popular movies: {str(e)}"
        )