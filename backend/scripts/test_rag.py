import sys
import os
import asyncio

# Setup path so Python finds the 'app' folder
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BACKEND_DIR)

from app.db.session import AsyncSessionLocal
from app.services.rag_service import rag_service
from app.services.embedder import embedder

async def test_rag():
    print("Loading embedder into VRAM...")
    embedder.load_model()
    
    # Let's pretend the LLM decided to search for this based on a user's prompt
    query = "Where can I find historical temples and good food in Japan?"
    print(f"\nSearching database for: '{query}'\n")
    
    async with AsyncSessionLocal() as db:
        # Call the Librarian!
        results = await rag_service.retrieve_relevant_chunks(db, query=query, limit=3)
        
        if not results:
            print("No results found. Did ingestion work?")
            return

        for i, chunk in enumerate(results, 1):
            destination = chunk.destination
            print(f"--- Result {i} | City: {destination.name} | Style: {destination.travel_style} ---")
            print(f"{chunk.content}...\n")

if __name__ == "__main__":
    asyncio.run(test_rag())