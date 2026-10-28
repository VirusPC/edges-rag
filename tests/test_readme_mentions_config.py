from pathlib import Path

README = Path(__file__).resolve().parents[1] / "README.md"


def test_readme_documents_required_env_and_ask():
    text = README.read_text(encoding="utf-8")
    for needle in [
        "INDEX_ROOT",
        "CHROMA_PERSIST_DIR",
        "OLLAMA_BASE_URL",
        "OLLAMA_EMBED_MODEL",
        "OLLAMA_CHAT_MODEL",
        "RAG_API_TOKEN",
        "POST /ask",
        "Bearer",
        "4070ts",
        "Tailscale",
    ]:
        assert needle in text, f"README missing {needle}"
