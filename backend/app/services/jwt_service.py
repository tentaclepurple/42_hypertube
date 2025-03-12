# backend/app/services/jwt_service.py


from datetime import datetime, timedelta
from typing import Optional
import jwt
import os
import uuid
from uuid import UUID


class JWTService:
    """Service for JWT token generation and validation"""
    
    SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super_secret_development_key")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
    
    @staticmethod
    def create_access_token(user_id: UUID, expires_delta: Optional[timedelta] = None):
        """
        Create a new JWT access token with JTI
        """
        jti = str(uuid.uuid4())
        
        to_encode = {"sub": str(user_id), "jti": jti}
        
        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=JWTService.ACCESS_TOKEN_EXPIRE_MINUTES)
            
        to_encode.update({"exp": expire})
        
        # Generate token
        encoded_jwt = jwt.encode(
            to_encode, 
            JWTService.SECRET_KEY, 
            algorithm=JWTService.ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str):
        """
        Verify a JWT token and return the user_id
        """
        try:
            payload = jwt.decode(
                token, 
                JWTService.SECRET_KEY, 
                algorithms=[JWTService.ALGORITHM]
            )
            
            user_id = payload.get("sub")
            if user_id is None:
                raise ValueError("Could not validate token - missing user ID")
                
            return user_id
        except jwt.PyJWTError as e:
            raise ValueError(f"Could not validate token: {str(e)}")
    
    @staticmethod
    def decode_token_without_verification(token: str):
        """
        Decode token without verifying signature to extract metadata
        """
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception as e:
            raise ValueError(f"Error decoding token: {str(e)}")