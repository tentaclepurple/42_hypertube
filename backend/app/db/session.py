# backend/app/db/session.py

import os
import asyncpg
import asyncio
from contextlib import asynccontextmanager


async def get_connection_pool():
    """Creates connection pool for PostgreSQL"""
    if not hasattr(get_connection_pool, "pool"):
        get_connection_pool.pool = await asyncpg.create_pool(
            os.environ.get("DATABASE_URL"),
            min_size=5,
            max_size=20,
            statement_cache_size=0
        )
    return get_connection_pool.pool


@asynccontextmanager
async def get_db_connection():
    """Context manager to get a conection from the pool"""
    pool = await get_connection_pool()
    async with pool.acquire() as connection:
        yield connection


async def test_connection():
    try:
        async with get_db_connection() as conn:
            version = await conn.fetchval("SELECT version()")
            print(f"Connection successful! PostgreSQL version: {version}")
    except Exception as e:
        print(f"Connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_connection())
