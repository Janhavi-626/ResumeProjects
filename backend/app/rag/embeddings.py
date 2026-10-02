import hashlib
import math
import re

from app.config.settings import get_settings


class LocalHashEmbeddings:
    """Deterministic, dependency-light fallback for demos without an API key."""

    dimensions = 384

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        for token in tokens:
            digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimensions
            vector[index] += 1.0 if digest[4] % 2 else -1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def get_embeddings():
    settings = get_settings()
    if settings.openai_api_key:
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=settings.openai_embedding_model, api_key=settings.openai_api_key)
    return LocalHashEmbeddings()