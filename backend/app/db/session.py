from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from typing import AsyncGenerator

# 1. Create the Async Engine (The Singleton)
# This stays alive for the life of the app
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True, # Set to False in production; True helps you see the SQL being run
    future=True
)

# 2. Create the Session Factory
# This is what generates a session for each request
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, # Crucial for async to prevent "greenlet" errors
)

# 3. The Dependency Injection function
# This is what we use in the FastAPI routes: Depends(get_db)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()