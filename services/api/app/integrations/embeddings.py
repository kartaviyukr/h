from typing import Protocol

from app.core.config import settings


class Embedder(Protocol):
    dim: int

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""
        ...


class LocalEmbedder:
    """sentence-transformers embedder. Requires the optional `rag` extra.

    The model is loaded lazily on first use so importing this module stays cheap
    and test environments without torch are unaffected.
    """

    def __init__(self, model_name: str, dim: int) -> None:
        self.model_name = model_name
        self.dim = dim
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: list[str]) -> list[list[float]]:
        model = self._load()
        vectors = model.encode(texts, normalize_embeddings=True)
        return [[float(x) for x in vec] for vec in vectors]


def get_embedder() -> Embedder:
    return LocalEmbedder(settings.embedding_model, settings.embedding_dim)
