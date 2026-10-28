import pytest
from llama_index.core.embeddings import BaseEmbedding

from edges_rag.config import get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class FakeEmbedding(BaseEmbedding):
    """Deterministic tiny embedding for tests (no Ollama)."""

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._hash_embed(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._hash_embed(text)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._hash_embed(query)

    async def _aget_text_embedding(self, text: str) -> list[float]:
        return self._hash_embed(text)

    def _hash_embed(self, text: str) -> list[float]:
        # 8-dim stable pseudo-embedding
        vals = [((ord(c) % 13) / 13.0) for c in (text[:8].ljust(8, " "))]
        return vals


@pytest.fixture
def fake_embed() -> FakeEmbedding:
    return FakeEmbedding()
