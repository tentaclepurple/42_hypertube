# backend/app/models/comment.py

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import uuid


class CommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000, description="Comment content")
    movie_id: uuid.UUID = Field(..., description="Movie ID")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5")
    
    @validator('comment')
    def validate_comment(cls, v):
        if not v or not v.strip():
            raise ValueError("Comment cannot be empty")
        return v.strip()


class CommentUpdate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000, description="Updated comment content")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Updated rating from 1 to 5")
    
    @validator('comment')
    def validate_comment(cls, v):
        if not v or not v.strip():
            raise ValueError("Comment cannot be empty")
        return v.strip()


class CommentResponse(BaseModel):
    id: str
    user_id: str
    movie_id: str
    comment: str
    rating: Optional[int]
    username: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    id: str
    comment: str
    rating: Optional[int]
    username: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CommentDetailResponse(BaseModel):
    id: str
    comment: str
    rating: Optional[int]
    username: str
    created_at: datetime
    
    class Config:
        from_attributes = True