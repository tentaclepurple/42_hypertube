# backend/app/services/api_key_service.py

import secrets
import bcrypt
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from app.db.session import get_db_connection
from app.services.jwt_service import JWTService

class ApiKeyService:
    """API Key Service for managing API keys and secrets."""    
    
    @staticmethod
    def get_current_time():
        """
        Returns the current time with UTC timezone
        """
        return datetime.now(timezone.utc)
    
    @staticmethod
    def generate_api_credentials() -> tuple[str, str]:
        """
        Generates a pair of api_key + api_secret
        """
        api_key = "ak_" + secrets.token_hex(12)      # ak_ + 24 chars
        api_secret = "as_" + secrets.token_hex(12)   # as_ + 24 chars
        return api_key, api_secret
    
    @staticmethod
    def hash_secret(secret: str) -> str:
        """
        Hashes the API secret for secure storage
        """
        return bcrypt.hashpw(secret.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_secret(secret: str, hashed_secret: str) -> bool:
        """
        Verifies an API secret against its hash
        """
        try:
            return bcrypt.checkpw(secret.encode('utf-8'), hashed_secret.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    async def create_api_key(user_id: str, name: str, expires_in_days: int = 30) -> Dict[str, Any]:
        """
        Creates a new API key for a user
        """
        api_key, api_secret = ApiKeyService.generate_api_credentials()
        secret_hash = ApiKeyService.hash_secret(api_secret)
        
        key_id = uuid.uuid4()
        now = ApiKeyService.get_current_time()
        expires_at = now + timedelta(days=expires_in_days)
        
        async with get_db_connection() as conn:
            result = await conn.fetchrow(
                """
                INSERT INTO api_keys 
                (id, user_id, key_name, api_key, api_secret_hash, is_active, expires_at, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)
                RETURNING id, user_id, key_name, api_key, is_active, expires_at, created_at, last_used_at, usage_count
                """,
                key_id, uuid.UUID(user_id), name, api_key, secret_hash, True, expires_at, now
            )
            
            return {
                "id": str(result["id"]),
                "name": result["key_name"],
                "api_key": result["api_key"],
                "api_secret": api_secret,
                "is_active": result["is_active"],
                "expires_at": result["expires_at"],
                "created_at": result["created_at"],
                "last_used_at": result["last_used_at"],
                "usage_count": result["usage_count"]
            }
    
    @staticmethod
    async def get_user_api_keys(user_id: str) -> List[Dict[str, Any]]:
        """
        Gets all API keys for a user
        """
        async with get_db_connection() as conn:
            results = await conn.fetch(
                """
                SELECT id, key_name, api_key, is_active, expires_at, created_at, last_used_at, usage_count
                FROM api_keys 
                WHERE user_id = $1 
                ORDER BY created_at DESC
                """,
                uuid.UUID(user_id)
            )
            
            return [
                {
                    "id": str(row["id"]),
                    "name": row["key_name"],
                    "api_key": row["api_key"],
                    "is_active": row["is_active"],
                    "expires_at": row["expires_at"],
                    "created_at": row["created_at"],
                    "last_used_at": row["last_used_at"],
                    "usage_count": row["usage_count"]
                }
                for row in results
            ]
    
    @staticmethod
    async def validate_api_credentials(api_key: str, api_secret: str) -> Optional[Dict[str, Any]]:
        """
        Validates API credentials and returns user information
        """
        async with get_db_connection() as conn:
            result = await conn.fetchrow(
                """
                SELECT ak.id, ak.user_id, ak.api_secret_hash, ak.is_active, ak.expires_at,
                       u.id as user_id, u.email, u.username, u.first_name, u.last_name
                FROM api_keys ak
                JOIN users u ON ak.user_id = u.id
                WHERE ak.api_key = $1
                """,
                api_key
            )
            
            if not result:
                return None

            # Check if the key is active
            if not result["is_active"]:
                return None

            # Check if it has expired
            if result["expires_at"]:
                # Ensure both datetime have timezone info
                expires_at = result["expires_at"]
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                
                current_time = ApiKeyService.get_current_time()
                
                if expires_at < current_time:
                    return None
            
            # check the secret
            if not ApiKeyService.verify_secret(api_secret, result["api_secret_hash"]):
                return None
            
            # update last used and usage count
            await conn.execute(
                """
                UPDATE api_keys 
                SET last_used_at = $1, usage_count = usage_count + 1, updated_at = $1
                WHERE id = $2
                """,
                ApiKeyService.get_current_time(), result["id"]
            )
            
            return {
                "api_key_id": str(result["id"]),
                "user_id": str(result["user_id"]),
                "email": result["email"],
                "username": result["username"],
                "first_name": result["first_name"],
                "last_name": result["last_name"]
            }
    
    @staticmethod
    async def revoke_api_key(user_id: str, api_key_id: str) -> bool:
        """
        Revokes (deactivates) an API key
        """
        async with get_db_connection() as conn:
            result = await conn.fetchrow(
                """
                UPDATE api_keys 
                SET is_active = false, updated_at = $1
                WHERE id = $2 AND user_id = $3
                RETURNING id
                """,
                ApiKeyService.get_current_time(), uuid.UUID(api_key_id), uuid.UUID(user_id)
            )
            
            return result is not None
    
    @staticmethod
    async def delete_api_key(user_id: str, api_key_id: str) -> bool:
        """
        Deletes an API key permanently
        """
        async with get_db_connection() as conn:
            result = await conn.fetchrow(
                """
                DELETE FROM api_keys 
                WHERE id = $1 AND user_id = $2
                RETURNING id
                """,
                uuid.UUID(api_key_id), uuid.UUID(user_id)
            )
            
            return result is not None