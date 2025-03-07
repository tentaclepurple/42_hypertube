# backend/app/models/users.py


from pydantic import BaseModel, EmailStr, Field, validator
import re
from typing import Optional
from datetime import datetime
from uuid import UUID
import uuid



class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    created_at: datetime
    

# Modelo para la actualización del perfil
class ProfileUpdate(BaseModel):
    birth_year: int = Field(..., ge=1900, le=datetime.now().year)
    gender: str = Field(..., min_length=1, max_length=20)
    bio: Optional[str] = None
    favorite_movie_id: Optional[uuid.UUID] = None
    worst_movie_id: Optional[uuid.UUID] = None
    movie_preference_a_id: Optional[uuid.UUID] = None
    movie_preference_b_id: Optional[uuid.UUID] = None
    movie_preference_c_id: Optional[uuid.UUID] = None
    movie_preference_d_id: Optional[uuid.UUID] = None
    email: Optional[str] = None
    
    @validator('birth_year')
    def validate_birth_year(cls, v):
        if v < 1900 or v > datetime.now().year:
            raise ValueError("Birth year must be between 1900 and current year")
        return v
