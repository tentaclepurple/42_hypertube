# backend/app/models/view_progress.py

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class ViewProgressUpdate(BaseModel):
    view_percentage: float = Field(..., ge=0.0, le=100.0, description="Viewing percentage (0-100)")
    
    @validator('view_percentage')
    def round_percentage(cls, v):
        return round(v, 2)

class ViewProgressResponse(BaseModel):
    movie_id: str
    user_id: str
    view_percentage: float
    completed: bool
    updated_at: datetime
    
    class Config:
        from_attributes = True