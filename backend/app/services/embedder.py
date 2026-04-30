import torch
from sentence_transformers import SentenceTransformer
from anyio import to_thread
from typing import List, Optional

class TravelEmbedder:
    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self):
        """Loads model into GPU VRAM. Called exactly once at startup."""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            # Warm up the model on the GPU (Great idea from your old code!)
            self.model.encode(["warmup"])

    async def embed_query(self, text: str) -> List[float]:
        """Wrap GPU call in a thread to remain non-blocking for FastAPI."""
        if self.model is None:
            raise RuntimeError("Model is not loaded. Ensure lifespan startup ran.")
        return await to_thread.run_sync(self._embed, text)

    def _embed(self, text: str) -> List[float]:
        return self.model.encode(text, convert_to_tensor=False).tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents efficiently using GPU batching."""
        if self.model is None:
            raise RuntimeError("Model is not loaded.")
        return await to_thread.run_sync(self._embed_batch, texts)

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, batch_size=32, convert_to_tensor=False).tolist()

# The Singleton Instance
embedder = TravelEmbedder()