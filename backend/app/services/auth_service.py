# backend/app/services/auth_service.py


from passlib.context import CryptContext
from app.models.users import UserCreate
from app.db.session import get_db_connection
import uuid
from datetime import datetime
from .queries import insert_user


# Configure password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    
    @staticmethod
    async def authenticate_user(username_or_email: str, password: str):
        """
        Authenticate a user with username/email and password
        """
        async with get_db_connection() as conn:
            # Try to find user by username or email
            user = await conn.fetchrow(
                """
                SELECT id, email, username, password, first_name, last_name, 
                    profile_picture, created_at
                FROM users 
                WHERE username = $1 OR email = $1
                """,
                username_or_email
            )
            
            if not user:
                raise ValueError("Invalid username or password")
            
            # Check if password exists (OAuth accounts might not have one)
            if not user["password"]:
                raise ValueError("This account uses OAuth authentication")
                
            # Verify password
            if not pwd_context.verify(password, user["password"]):
                raise ValueError("Invalid username or password")
            
            # Return user without password
            user_dict = dict(user)
            user_dict.pop("password", None)
            
            return user_dict


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
    
