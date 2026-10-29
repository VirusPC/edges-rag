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


def test_assistant_page_public_name(tmp_path: Path):
    settings = Settings(
        INDEX_ROOT=str(tmp_path),
        CHROMA_PERSIST_DIR=str(tmp_path / "chroma"),
        OLLAMA_BASE_URL="http://127.0.0.1:9",
        OLLAMA_EMBED_MODEL="fake",
        OLLAMA_CHAT_MODEL="fake",
        RAG_API_TOKEN="test-token",
    )
    client = TestClient(create_app(settings=settings, skip_lifespan_index=True))
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert "<title>Edges 小助手</title>" in body
    assert "<h1>Edges 小助手</h1>" in body
    assert "索引 VirusPC/edges 框架仓，公开可问" in body
    assert "https://edges-rag.viruspc.tech/" in body
    assert "/api/ask" in body
    assert "LIVE_ORIGINS" in body
    assert "备用入口（Tailscale）" in body
    assert "仅限 Tailscale" not in body
    assert "试用" not in body
    assert "4070ts" not in body
    assert body.index("公开可问") < body.index("100.67.197.1")
    denied = client.post("/ask", json={"question": "Edges 是什么？"})
    assert denied.status_code == 401


def test_ask_unauthorized_wrong_token(tmp_path: Path, fake_embed):
    client, _ = _build_client(tmp_path, fake_embed)
    resp = client.post(
        "/ask",
        headers={"Authorization": "Bearer wrong"},
        json={"question": "What is Edges?"},
    )
    assert resp.status_code == 401
