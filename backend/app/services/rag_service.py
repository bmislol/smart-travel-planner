from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import DestinationChunk
from app.services.embedder import TravelEmbedder, embedder
from typing import List

class RAGService:
    def __init__(self, embedder_instance: TravelEmbedder):
        # We inject the embedder here so the service has its "brain"
        self.embedder = embedder_instance

    async def retrieve_relevant_chunks(
        self, 
        db: AsyncSession, 
        query: str, 
        limit: int = 5
    ) -> List[DestinationChunk]:
        """
        Takes a natural language query, embeds it, and searches Postgres chunks.
        """
        # 1. Convert user query to a vector (Non-blocking GPU call)
        query_vector = await self.embedder.embed_query(query)

        # 2. Perform semantic search using pgvector on the chunks
        stmt = (
            select(DestinationChunk)
            .options(selectinload(DestinationChunk.destination)) # Eagerly load the parent destination!
            .order_by(DestinationChunk.embedding.cosine_distance(query_vector))
            .limit(limit)
        )

        result = await db.execute(stmt)
        return result.scalars().all()

# Instantiate the service singleton using our global embedder
rag_service = RAGService(embedder)