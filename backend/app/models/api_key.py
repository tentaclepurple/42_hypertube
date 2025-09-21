# backend/app/models/api_key.py

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name for this API key")
    expires_in_days: Optional[int] = Field(30, ge=1, le=365, description="Expiration in days (1-365)")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("API key name cannot be empty")
        return v.strip()

class ApiKeyResponse(BaseModel):
    id: str
    name: str
    api_key: str
    api_secret: str
    is_active: bool
    expires_at: datetime
    created_at: datetime
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    
    class Config:
        from_attributes = True

class ApiKeyListResponse(BaseModel):
    id: str
    name: str
    api_key: str
    is_active: bool
    expires_at: datetime
    created_at: datetime
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    
    class Config:
        from_attributes = True

class OAuthTokenRequest(BaseModel):
    grant_type: str = Field(..., description="Must be 'api_key'")
    api_key: str = Field(..., min_length=1, description="API key")
    api_secret: str = Field(..., min_length=1, description="API secret")
    
    @validator('grant_type')
    def validate_grant_type(cls, v):
        if v != 'api_key':
            raise ValueError("grant_type must be 'api_key'")
        return v

class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str = "api"