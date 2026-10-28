from pathlib import Path

from fastapi.testclient import TestClient
from llama_index.core.llms import CompletionResponse, CustomLLM, LLMMetadata
from llama_index.core.llms.callbacks import llm_completion_callback

from edges_rag.app import create_app
from edges_rag.config import Settings
from edges_rag.index_store import IndexStore
from edges_rag.query_engine import QueryService


class FakeLLM(CustomLLM):
    model_name: str = "fake-chat"

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(model_name=self.model_name)

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs):
        return CompletionResponse(text="Edges compose add mounts harness repos.")

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs):
        raise NotImplementedError


def _build_client(tmp_path: Path, fake_embed, token: str = "test-token"):
    root = tmp_path / "edges"
    root.mkdir()
    (root / "README.md").write_text(
        "Edges is a framework for agent harness composition.",
        encoding="utf-8",
    )
    settings = Settings(
        INDEX_ROOT=str(root),
        CHROMA_PERSIST_DIR=str(tmp_path / "chroma"),
        OLLAMA_BASE_URL="http://127.0.0.1:9",
        OLLAMA_EMBED_MODEL="fake",
        OLLAMA_CHAT_MODEL="fake",
        RAG_API_TOKEN=token,
        RAG_TOP_K=3,
    )
    store = IndexStore(settings, embed_model=fake_embed)
    store.build_full()
    svc = QueryService(store, settings, llm=FakeLLM())
    app = create_app(
        settings=settings,
        query_service=svc,
        skip_lifespan_index=True,
    )
    return TestClient(app), token


def test_ask_happy_path(tmp_path: Path, fake_embed):
    client, token = _build_client(tmp_path, fake_embed)
    resp = client.post(
        "/ask",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "What is Edges?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "citations" in data
    assert isinstance(data["citations"], list)
    assert "Edges" in data["answer"] or "compose" in data["answer"].lower()
    if data["citations"]:
        assert "path" in data["citations"][0]
        assert "snippet" in data["citations"][0]
        assert "score" in data["citations"][0]


def test_ask_unauthorized_missing_token(tmp_path: Path, fake_embed):
    client, _ = _build_client(tmp_path, fake_embed)
    resp = client.post("/ask", json={"question": "What is Edges?"})
    assert resp.status_code == 401


def test_ask_unauthorized_wrong_token(tmp_path: Path, fake_embed):
    client, _ = _build_client(tmp_path, fake_embed)
    resp = client.post(
        "/ask",
        headers={"Authorization": "Bearer wrong"},
        json={"question": "What is Edges?"},
    )
    assert resp.status_code == 401
