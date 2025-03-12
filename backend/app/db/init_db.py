# backend/app/db/init_db.py

import asyncio
import os

from session import get_db_connection
from queries import create_users_table, create_users_idx


async def create_tables():
    """
    Create tables if they don't exist.
    """
    try:
        async with get_db_connection() as conn:
            # Create users table if it doesn't exist
            await conn.execute(create_users_table)
            
            # Create indexes for faster lookups
            await conn.execute(create_users_idx)
            
            print("Tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")


if __name__ == "__main__":
    asyncio.run(create_tables())
