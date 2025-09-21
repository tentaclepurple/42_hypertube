# backend/app/services/token_service.py


from app.db.session import get_db_connection
import jwt
from datetime import datetime, timedelta

class TokenService:
    @staticmethod
    async def revoke_token(token: str, user_id, reason: str = "user_logout") -> bool:
        """
        Revoke a JWT token by adding it to the revoked tokens table
        """
        try:
            # Extract the jti (JWT ID) from the token
            payload = jwt.decode(token, options={"verify_signature": False})
            token_jti = payload.get('jti')
            
            if not token_jti:
                print("No jti claim found in token", flush=True)
                return False

            # Check if the token is already revoked
            async with get_db_connection() as conn:
                exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM revoked_tokens WHERE jti = $1)",
                    token_jti
                )
                
                if exists:
                    # The token is already revoked, do nothing
                    return True

                # Calculate the expiration date if available in the token
                expiry = None
                if 'exp' in payload:
                    # The 'exp' field in JWT is a UNIX timestamp in seconds
                    exp_timestamp = payload['exp']
                    expiry = datetime.fromtimestamp(exp_timestamp)
                else:
                    # If there is no expiration date in the token, set a default (7 days)
                    expiry = datetime.now() + timedelta(days=7)

                # Insert into the revoked tokens table using the jti column
                await conn.execute(
                    """
                    INSERT INTO revoked_tokens (jti, user_id, revoked_at, expiry)
                    VALUES ($1, $2, $3, $4)
                    """,
                    token_jti, user_id, datetime.now(), expiry
                )

                print(f"Token revoked successfully", flush=True)
                return True
                
        except Exception as e:
            print(f"Error revoking token: {str(e)}", flush=True)
            return False
    
    @staticmethod
    async def is_token_revoked(token: str) -> bool:
        """
        Check if a token is revoked
        """
        try:
            # Extract the jti (JWT ID) from the token
            payload = jwt.decode(token, options={"verify_signature": False})
            token_jti = payload.get('jti')
            
            if not token_jti:
                # If there is no jti, we cannot check if it is revoked
                return False

            # Check in the database if the token is revoked using the jti column
            async with get_db_connection() as conn:
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM revoked_tokens WHERE jti = $1)",
                    token_jti
                )
                
                return result
        except Exception as e:
            print(f"Error checking token revocation: {str(e)}", flush=True)
            # In case of error, we allow the token to remain valid
            return False
    
    @staticmethod
    async def clean_expired_tokens():
        """
        Remove expired tokens from the blacklist to keep the table optimized
        """
        try:
            async with get_db_connection() as conn:
                result = await conn.execute(
                    "DELETE FROM revoked_tokens WHERE expiry < NOW()"
                )
            print(f"Cleaned expired tokens from blacklist")
            return True
        except Exception as e:
            print(f"Error cleaning expired tokens: {str(e)}")
            return False