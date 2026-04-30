import sys
import os

# 1. Setup path so Python finds the 'app' folder
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BACKEND_DIR)

import asyncio
import json
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 2. When this imports session, session imports config, and config handles the .env!
from app.db.session import AsyncSessionLocal, engine
from app.db.models import Base, Destination, DestinationChunk
from app.services.embedder import embedder

# Path to your unstructured text data
RAG_DATA_PATH = os.path.join(os.path.dirname(__file__), "../../data/raw/travel_guides.json")

async def init_db():
    """Creates the vector extension and all database tables."""
    print("Initializing database tables...")
    async with engine.begin() as conn:
        # pgvector requires this extension to exist before creating Vector columns
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        # Create all tables defined in our models
        await conn.run_sync(Base.metadata.create_all)

async def clear_existing_data(session: AsyncSession):
    """Clears existing RAG data to prevent duplicates during testing."""
    print("Clearing existing destinations and chunks...")
    await session.execute(delete(Destination))
    await session.commit()

async def ingest_knowledge_base():
    print("Starting RAG Ingestion Process...")
    
    embedder.load_model()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
    )

    if not os.path.exists(RAG_DATA_PATH):
        print(f"Error: Could not find RAG data at {RAG_DATA_PATH}")
        return

    with open(RAG_DATA_PATH, "r", encoding="utf-8") as f:
        destinations_data = json.load(f)

    async with AsyncSessionLocal() as session:
        await clear_existing_data(session)
        
        for dest_data in destinations_data:
            print(f"Processing: {dest_data['name']}...")
            
            destination = Destination(
                name=dest_data['name'],
                description=dest_data['description'],
                travel_style=dest_data['travel_style']
            )
            session.add(destination)
            await session.flush() 
            
            chunks = text_splitter.split_text(dest_data['description'])
            
            print(f"  Embedding {len(chunks)} chunks...")
            embeddings = await embedder.embed_batch(chunks)
            
            for chunk_text, embedding_vector in zip(chunks, embeddings):
                chunk_record = DestinationChunk(
                    destination_id=destination.id,
                    content=chunk_text,
                    embedding=embedding_vector
                )
                session.add(chunk_record)
                
        await session.commit()
        print("\nIngestion Complete! Data successfully vectorized and stored in Postgres.")

async def main():
    try:
        await init_db()  # <-- Build the tables first!
        await ingest_knowledge_base()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())