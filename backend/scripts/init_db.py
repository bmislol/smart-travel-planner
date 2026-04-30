import sys
import os
import asyncio

# Setup path so Python finds the 'app' folder
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BACKEND_DIR)

from app.db.session import engine
from app.db.models import Base

# By importing ALL models here, SQLAlchemy will see them and create the tables.
from app.db.models import User, Chat, AgentLog, Destination, DestinationChunk

async def init_tables():
    print("Creating missing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_tables())