import asyncio
import sys
from pathlib import Path

# Ensure the script can see the 'app' module
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db.session import AsyncSessionLocal
from app.db.models import Destination
from app.core.config import settings
from app.services.embedder import TravelEmbedder
from app.services.data_utils import load_and_chunk_csv

async def main():
    print("🚀 Starting Ingestion to Postgres...")
    embedder = TravelEmbedder(settings.EMBEDDING_MODEL_NAME)
    chunks = load_and_chunk_csv("../data/cleaned/expanded_travel_data.csv")
    
    async with AsyncSessionLocal() as session:
        for i in range(0, len(chunks), 50): # Batch size 50
            batch = chunks[i : i + 50]
            texts = [c["text"] for c in batch]
            embeddings = await embedder.embed_batch(texts)
            
            for idx, chunk in enumerate(batch):
                dest = Destination(
                    name=chunk["metadata"]["city"],
                    description=chunk["text"],
                    travel_style=chunk["metadata"]["label"],
                    embedding=embeddings[idx]
                )
                session.add(dest)
            
            await session.commit()
            print(f"✅ Ingested {i + len(batch)} / {len(chunks)}")

if __name__ == "__main__":
    asyncio.run(main())