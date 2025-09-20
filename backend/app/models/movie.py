# backend/app/models/movie.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class DownloadRequest(BaseModel):
    hash: str = Field(..., min_length=40, max_length=40, description="Torrent hash")


class TorrentInfo(BaseModel):
    url: Optional[str] = None
    hash: Optional[str] = None
    quality: Optional[str] = None
    type: Optional[str] = None
    seeds: Optional[int] = 0
    peers: Optional[int] = 0
    size: Optional[str] = None
    size_bytes: Optional[int] = 0

class MovieSearchResponse(BaseModel):
    id: str
    imdb_id: Optional[str] = None
    title: str
    year: Optional[int] = None
    rating: Optional[float] = None
    genres: List[str] = []
    summary: Optional[str] = ""
    poster: Optional[str] = None
    torrents: Optional[List[Dict[str, Any]]] = None
    torrent_hash: Optional[str] = None
    source: Optional[str] = None
    runtime: Optional[int] = None

class MovieDetail(BaseModel):
    id: str
    imdb_id: Optional[str] = None
    title: str
    year: Optional[int] = None
    rating: Optional[float] = None
    runtime: Optional[int] = None
    genres: List[str] = []
    summary: str = ""
    poster: Optional[str] = None
    director: List[str] = []
    cast: List[str] = []
    torrents: Optional[List[Dict[str, Any]]] = None
    torrent_hash: Optional[str] = None
    download_status: Optional[str] = None
    download_progress: Optional[int] = 0
    hypertube_rating: Optional[float] = None
    view_percentage: float = 0.0
    completed: bool = False

class MovieBasicResponse(BaseModel):
    id: str
    title: str
    poster: Optional[str] = None
    year: Optional[int] = None
    rating: Optional[float] = None
    genres: List[str] = []  # ← Agregar esta línea
    # Campos para visualización
    view_percentage: float = 0.0
    completed: bool = False

class PublicMovieResponse(BaseModel):
    id: str
    title: str
    year: Optional[int] = None
    imdb_rating: Optional[float] = None
    hypertube_rating: Optional[float] = None
    poster: Optional[str] = None
    genres: List[str] = []