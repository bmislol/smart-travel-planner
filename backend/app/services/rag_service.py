from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Destination
from app.services.embedder import TravelEmbedder
from typing import List

class RAGService:
    def __init__(self, embedder: TravelEmbedder):
        # We inject the embedder here so the service has its "brain"
        self.embedder = embedder

    async def retrieve_relevant_destinations(
        self, 
        db: AsyncSession, 
        query: str, 
        limit: int = 5
    ) -> List[Destination]:
        """
        Takes a natural language query, embeds it, and searches Postgres.
        """
        # 1. Convert user query to a vector (Non-blocking GPU call)
        query_vector = await self.embedder.embed_query(query)

        # 2. Perform semantic search using pgvector
        # We use cosine_distance as per common RAG standards
        stmt = (
            select(Destination)
            .order_by(Destination.embedding.cosine_distance(query_vector))
            .limit(limit)
        )

        result = await db.execute(stmt)
        # return the actual database objects
        return result.scalars().all()