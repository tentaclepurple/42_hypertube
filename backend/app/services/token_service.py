# backend/app/services/token_service.py
from datetime import datetime
import jwt
import uuid
from app.db.session import get_db_connection


class TokenService:
    @staticmethod
    async def revoke_token(token: str, user_id: uuid.UUID, reason: str = "user_logout"):
        """
        Revocar un token agregándolo a la blacklist
        """
        try:
            # Decodificar el token sin verificar firma para extraer metadatos
            from app.services.jwt_service import JWTService
            payload = JWTService.decode_token_without_verification(token)
            
            # Extraer datos necesarios
            jti = payload.get("jti")
            exp = datetime.fromtimestamp(payload.get("exp"))
            
            if not jti:
                raise ValueError("Token doesn't contain a JTI")
            
            # Almacenar en la base de datos
            async with get_db_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO revoked_tokens 
                    (token_jti, user_id, expiry, revoked_by)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (jti) DO NOTHING
                    """,
                    jti, user_id, exp, reason
                )
                
            return True
        except Exception as e:
            print(f"Error revoking token: {str(e)}")
            return False
    
    @staticmethod
    async def is_token_revoked(token: str) -> bool:
        """
        Verificar si un token está en la blacklist
        """
        try:
            # Decodificar sin verificar para obtener el JTI
            from app.services.jwt_service import JWTService
            payload = JWTService.decode_token_without_verification(token)
            jti = payload.get("jti")
            
            if not jti:
                return False  # Si no tiene JTI, no puede estar en la blacklist
            
            # Verificar en la base de datos
            async with get_db_connection() as conn:
                is_revoked = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM revoked_tokens WHERE token_id = $1)",
                    jti
                )
                
            return is_revoked
        except Exception as e:
            print(f"Error checking token revocation: {str(e)}")
            return False  # Por defecto, permitir el acceso en caso de error
    
    @staticmethod
    async def clean_expired_tokens():
        """
        Eliminar tokens expirados de la blacklist para mantener la tabla optimizada
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