import time
from pathlib import Path

from edges_rag.config import Settings
from edges_rag.index_store import IndexStore
from edges_rag.watcher import IndexEventHandler, start_watcher


def _settings(tmp_path: Path) -> Settings:
    root = tmp_path / "edges"
    root.mkdir()
    (root / "seed.md").write_text("seed", encoding="utf-8")
    return Settings(
        INDEX_ROOT=str(root),
        CHROMA_PERSIST_DIR=str(tmp_path / "chroma"),
        OLLAMA_BASE_URL="http://127.0.0.1:9",
        OLLAMA_EMBED_MODEL="fake",
        OLLAMA_CHAT_MODEL="fake",
        RAG_API_TOKEN="tok",
    )


def test_handler_upsert_and_delete(tmp_path: Path, fake_embed):
    settings = _settings(tmp_path)
    store = IndexStore(settings, embed_model=fake_embed)
    store.build_full()
    handler = IndexEventHandler(store)

    new_path = settings.index_root / "watched.md"
    new_path.write_text("watched content", encoding="utf-8")
    # Simulate watchdog event without sleeping on FS notify
    from watchdog.events import FileCreatedEvent, FileDeletedEvent

    handler.on_created(FileCreatedEvent(str(new_path)))
    assert store.has_path("watched.md") is True

    handler.on_deleted(FileDeletedEvent(str(new_path)))
    assert store.has_path("watched.md") is False


def test_start_watcher_processes_new_file(tmp_path: Path, fake_embed):
    settings = _settings(tmp_path)
    store = IndexStore(settings, embed_model=fake_embed)
    store.build_full()
    observer = start_watcher(store)
    try:
        new_path = settings.index_root / "live.md"
        new_path.write_text("live", encoding="utf-8")
        deadline = time.time() + 5.0
        while time.time() < deadline and not store.has_path("live.md"):
            time.sleep(0.1)
        assert store.has_path("live.md") is True
    finally:
        observer.stop()
        observer.join(timeout=5)
