import os
from pathlib import Path

import pytest

from edges_rag.config import Settings, get_settings, parse_exclude_dirs, parse_extensions


def test_parse_extensions_normalizes():
    assert parse_extensions(".MD, txt, .Py") == [".md", ".txt", ".py"]


def test_parse_exclude_dirs():
    assert parse_exclude_dirs("node_modules, .git ,dist") == {
        "node_modules",
        ".git",
        "dist",
    }


def test_settings_from_env(monkeypatch, tmp_path: Path):
    get_settings.cache_clear()
    monkeypatch.setenv("INDEX_ROOT", str(tmp_path / "edges"))
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://4070ts-win11:11434")
    monkeypatch.setenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    monkeypatch.setenv("OLLAMA_CHAT_MODEL", "llama3.2")
    monkeypatch.setenv("RAG_API_TOKEN", "secret-token")
    monkeypatch.setenv(
        "INDEX_ALLOW_EXTENSIONS",
        ".md,.txt,.py,.ts,.tsx,.js,.jsx,.json,.yaml,.yml,.toml,.sh,.rs,.go",
    )
    monkeypatch.setenv(
        "INDEX_EXCLUDE_DIRS",
        "node_modules,.git,__pycache__,.venv,dist,build",
    )

    s = get_settings()
    assert s.index_root == tmp_path / "edges"
    assert s.chroma_persist_dir == tmp_path / "chroma"
    assert s.ollama_base_url == "http://4070ts-win11:11434"
    assert s.rag_api_token == "secret-token"
    assert s.rag_top_k == 5
    assert ".md" in s.index_allow_extensions
    assert "node_modules" in s.index_exclude_dirs


def test_settings_missing_required_raises(monkeypatch, tmp_path: Path):
    get_settings.cache_clear()
    for key in list(os.environ):
        if key.startswith(("INDEX_", "CHROMA_", "OLLAMA_", "RAG_")):
            monkeypatch.delenv(key, raising=False)
    with pytest.raises(Exception):
        Settings()  # type: ignore[call-arg]
