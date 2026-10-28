from pathlib import Path
from typing import Any

from llama_index.core.llms import CompletionResponse, CustomLLM, LLMMetadata
from llama_index.core.llms.callbacks import llm_completion_callback

from edges_rag.config import Settings
from edges_rag.index_store import IndexStore
from edges_rag.query_engine import QueryService
from edges_rag.schemas import AskResponse


class FakeLLM(CustomLLM):
    model_name: str = "fake-chat"

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(model_name=self.model_name)

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        return CompletionResponse(text="compose mounts harness repos")

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any):
        raise NotImplementedError


def _settings(tmp_path: Path) -> Settings:
    root = tmp_path / "edges"
    root.mkdir()
    (root / "skills" / "compose.md").parent.mkdir(parents=True)
    (root / "skills" / "compose.md").write_text(
        "edges compose add mounts an external harness repo into scope.",
        encoding="utf-8",
    )
    return Settings(
        INDEX_ROOT=str(root),
        CHROMA_PERSIST_DIR=str(tmp_path / "chroma"),
        OLLAMA_BASE_URL="http://127.0.0.1:9",
        OLLAMA_EMBED_MODEL="fake",
        OLLAMA_CHAT_MODEL="fake",
        RAG_API_TOKEN="tok",
        RAG_TOP_K=3,
    )


def test_ask_returns_answer_and_citations(tmp_path: Path, fake_embed):
    settings = _settings(tmp_path)
    store = IndexStore(settings, embed_model=fake_embed)
    store.build_full()
    svc = QueryService(store, settings, llm=FakeLLM())
    result = svc.ask("How does compose add work?")
    assert isinstance(result, AskResponse)
    assert "compose" in result.answer.lower()
    assert len(result.citations) >= 1
    cite = result.citations[0]
    assert cite.path == "skills/compose.md"
    assert len(cite.snippet) > 0
    assert cite.snippet.endswith("…") or len(cite.snippet) <= 240
