# backend/app/models/user_activity.py

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class FavoriteResponse(BaseModel):
    user_id: str
    movie_id: str
    created_at: datetime

class FavoriteMovieResponse(BaseModel):
    id: str
    title: str
    poster: Optional[str] = None
    year: Optional[int] = None
    rating: Optional[float] = None
    genres: List[str] = []
    created_at: datetime  # Cuando se añadió a favoritos

class ContinueWatchingResponse(BaseModel):
    id: str
    title: str
    poster: Optional[str] = None
    year: Optional[int] = None
    rating: Optional[float] = None
    genres: List[str] = []
    view_percentage: float
    last_viewed_at: datetime

class UserActivitySummary(BaseModel):
    favorites_count: int
    continue_watching_count: int
    completed_movies: int
    total_watch_time_minutes: Optional[int] = None