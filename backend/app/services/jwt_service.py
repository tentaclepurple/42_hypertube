# backend/app/services/jwt_service.py
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os
from uuid import UUID


class JWTService:
    """Service for JWT token generation and validation"""
    
    SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super_secret_development_key")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
    
    @staticmethod
    def create_access_token(user_id: UUID, expires_delta: Optional[timedelta] = None):
        """
        Create a new JWT access token
        
        Args:
            user_id: User ID to include in the token
            expires_delta: Optional custom expiration time
            
        Returns:
            str: Encoded JWT
        """
        to_encode = {"sub": str(user_id)}
        
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
        
        Args:
            token: JWT token to verify
            
        Returns:
            str: User ID from the token
            
        Raises:
            ValueError: If token is invalid or expired
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