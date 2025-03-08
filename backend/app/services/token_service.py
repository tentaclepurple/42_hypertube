# backend/app/services/token_service.py


from app.db.session import get_db_connection
import jwt
from datetime import datetime, timedelta

class TokenService:
    @staticmethod
    async def revoke_token(token: str, user_id, reason: str = "user_logout") -> bool:
        """
        Revoca un token añadiéndolo a la lista negra
        """
        try:
            # Extraer el jti (JWT ID) del token
            payload = jwt.decode(token, options={"verify_signature": False})
            token_jti = payload.get('jti')
            
            if not token_jti:
                print("No jti claim found in token", flush=True)
                return False
            
            print(f"Token JTI: {token_jti}", flush=True)
            
            # Verificar si el token ya está revocado
            async with get_db_connection() as conn:
                exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM revoked_tokens WHERE jti = $1)",
                    token_jti
                )
                
                if exists:
                    # El token ya está revocado, no hacemos nada
                    return True
                
                # Calcular la fecha de expiración si está disponible en el token
                expiry = None
                if 'exp' in payload:
                    # El campo 'exp' en JWT es un timestamp UNIX en segundos
                    exp_timestamp = payload['exp']
                    expiry = datetime.fromtimestamp(exp_timestamp)
                else:
                    # Si no hay fecha de expiración en el token, establecemos una por defecto (7 días)
                    expiry = datetime.now() + timedelta(days=7)
                
                # Insertar en la tabla de tokens revocados usando la columna jti
                await conn.execute(
                    """
                    INSERT INTO revoked_tokens (jti, user_id, revoked_at, expiry)
                    VALUES ($1, $2, $3, $4)
                    """,
                    token_jti, user_id, datetime.now(), expiry
                )
                
                print(f"Token revocado exitosamente", flush=True)
                return True
                
        except Exception as e:
            print(f"Error revoking token: {str(e)}", flush=True)
            # A pesar del error, permitimos que el logout continúe
            return False
    
    @staticmethod
    async def is_token_revoked(token: str) -> bool:
        """
        Verifica si un token está revocado
        """
        try:
            # Extraer el jti (JWT ID) del token
            payload = jwt.decode(token, options={"verify_signature": False})
            token_jti = payload.get('jti')
            
            if not token_jti:
                # Si no hay jti, no podemos verificar si está revocado
                return False
                
            # Verificar en la base de datos si el token está revocado usando la columna jti
            async with get_db_connection() as conn:
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM revoked_tokens WHERE jti = $1)",
                    token_jti
                )
                
                return result
        except Exception as e:
            print(f"Error checking token revocation: {str(e)}", flush=True)
            # En caso de error, permitimos que el token siga siendo válido
            return False
    
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