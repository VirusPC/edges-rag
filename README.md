# edges-rag

Knowledge Q&A agent for the **Edges framework** official tree ([VirusPC/edges](https://github.com/VirusPC/edges)), indexed from a composed checkout on **minigtr**. Not for personal brain/workspace dumps.

Design: `docs/superpowers/specs/2026-10-28-edges-rag-design.md`

## Requirements

- Python 3.11+
- Ollama on **4070ts** reachable over **Tailscale** (`OLLAMA_BASE_URL`)
- A composed edges tree path for `INDEX_ROOT` (e.g. `…/.harness/compose/edges`)

## Quick start (minigtr)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# edit .env — set INDEX_ROOT, OLLAMA_BASE_URL, RAG_API_TOKEN, models
python -m edges_rag
```

On startup the service full-scans `INDEX_ROOT`, embeds via Ollama, persists Chroma under `CHROMA_PERSIST_DIR`, then watches for file changes.

## Environment

| Variable | Example | Notes |
|----------|---------|-------|
| `INDEX_ROOT` | `/home/you/ws/.harness/compose/edges` | Tree to index/watch |
| `EDGES_ROOT` | same as INDEX_ROOT | Optional alias |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | Local Chroma persist |
| `OLLAMA_BASE_URL` | `http://4070ts-win11:11434` | Tailscale hostname or IP |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Must exist on Ollama host |
| `OLLAMA_CHAT_MODEL` | `llama3.2` | Must exist on Ollama host |
| `RAG_API_TOKEN` | (secret) | Bearer token for API |
| `RAG_TOP_K` | `5` | Retrieval depth |
| `RAG_HOST` / `RAG_PORT` | `0.0.0.0` / `8000` | Bind address |
| `INDEX_ALLOW_EXTENSIONS` | `.md,.txt,.py,…` | See `.env.example` |
| `INDEX_EXCLUDE_DIRS` | `node_modules,.git,…` | See `.env.example` |

## Edges 小助手

`GET /` serves `src/edges_rag/static/index.html`. The public title is **Edges 小助手**. The page posts questions to same-origin `POST /api/ask`.

`POST /ask` stays on this service and still requires `Authorization: Bearer <RAG_API_TOKEN>`. The public front should keep injecting that token when it forwards `/api/ask`.

https://edges-rag.viruspc.tech/ is served by that front. On minigtr, pull `main`, point the front at `src/edges_rag/static/index.html` (or proxy `GET /` here), then restart the process that serves the HTML.

## API

`POST /ask` with header `Authorization: Bearer <RAG_API_TOKEN>`:

```bash
curl -s http://127.0.0.1:8000/ask \
  -H "Authorization: Bearer $RAG_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"How does edges compose add work?"}'
```

Response shape:

```json
{
  "answer": "…",
  "citations": [{"path": "skills/edges-compose/SKILL.md", "snippet": "…", "score": 0.81}]
}
```

Missing or wrong Bearer token → HTTP 401.

## Tests

```bash
pytest -v
```

Tests mock Ollama and use a temporary Chroma directory.

## Optional Docker Compose

`docker-compose.yml` mounts `INDEX_ROOT` and the Chroma data dir. Prefer bare venv on minigtr until container networking to Tailscale Ollama is verified.
