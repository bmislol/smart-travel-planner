import torch
from sentence_transformers import SentenceTransformer
from anyio import to_thread
from typing import List

class TravelEmbedder:
    def __init__(self, model_name: str):
        # Detect RTX 3060 for hardware acceleration
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=self.device)
        # Warm up the model on the GPU
        self.model.encode(["warmup"])

    async def embed_query(self, text: str) -> List[float]:
        """Wrap GPU call in a thread to remain non-blocking for FastAPI."""
        return await to_thread.run_sync(self._embed, text)

    def _embed(self, text: str) -> List[float]:
        return self.model.encode(text, convert_to_tensor=False).tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents efficiently using GPU batching."""
        return await to_thread.run_sync(self._embed_batch, texts)

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, batch_size=32, convert_to_tensor=False).tolist()