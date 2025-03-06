# backend/app/services/auth_service.py


from passlib.context import CryptContext
from app.models.user import UserCreate
from app.db.session import get_db_connection
import uuid
from datetime import datetime
from queries import insert_user


# Configure password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    async def create_user(user_data: UserCreate):
        """
        Creates a new user in the database.
        """
        # Generate UUID for the new user
        user_id = uuid.uuid4()
        
        # Hash the password
        hashed_password = pwd_context.hash(user_data.password)
        
        async with get_db_connection() as conn:
            # Check if email already exists
            email_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE email = $1)",
                user_data.email
            )
            
            if email_exists:
                raise ValueError("Email is already registered")
            
            # Check if username already exists
            username_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE username = $1)",
                user_data.username
            )
            
            if username_exists:
                raise ValueError("Username is already taken")
            
            # Insert the new user
            user = await conn.fetchrow(
                insert_user,
                user_id,
                user_data.email,
                user_data.username,
                hashed_password,
                user_data.first_name,
                user_data.last_name,
                datetime.now()
            )
            
            # Convert the database record to a dictionary
            return dict(user)
