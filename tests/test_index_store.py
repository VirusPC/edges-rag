from pathlib import Path

from edges_rag.config import Settings
from edges_rag.index_store import IndexStore


def _settings(tmp_path: Path) -> Settings:
    root = tmp_path / "edges"
    root.mkdir()
    (root / "a.md").write_text("alpha doc about compose", encoding="utf-8")
    (root / "b.md").write_text("beta doc about tasks", encoding="utf-8")
    return Settings(
        INDEX_ROOT=str(root),
        CHROMA_PERSIST_DIR=str(tmp_path / "chroma"),
        OLLAMA_BASE_URL="http://127.0.0.1:9",
        OLLAMA_EMBED_MODEL="fake",
        OLLAMA_CHAT_MODEL="fake",
        RAG_API_TOKEN="tok",
    )


def test_build_full_indexes_documents(tmp_path: Path, fake_embed):
    settings = _settings(tmp_path)
    store = IndexStore(settings, embed_model=fake_embed)
    n = store.build_full()
    assert n == 2
    assert store.has_path("a.md") is True
    assert store.has_path("b.md") is True
    assert store.has_path("missing.md") is False


def test_upsert_and_delete_by_path(tmp_path: Path, fake_embed):
    settings = _settings(tmp_path)
    store = IndexStore(settings, embed_model=fake_embed)
    store.build_full()

    new_file = settings.index_root / "c.md"
    new_file.write_text("gamma", encoding="utf-8")
    store.upsert_file(new_file)
    assert store.has_path("c.md") is True

    store.delete_file(new_file)
    assert store.has_path("c.md") is False
