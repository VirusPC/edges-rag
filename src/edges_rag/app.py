from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from edges_rag.auth import verify_bearer
from edges_rag.config import Settings, get_settings
from edges_rag.index_store import IndexStore
from edges_rag.query_engine import QueryService
from edges_rag.schemas import AskRequest, AskResponse
from edges_rag.watcher import start_watcher

_bearer_scheme = HTTPBearer(auto_error=False)


def create_app(
    settings: Settings | None = None,
    query_service: QueryService | None = None,
    skip_lifespan_index: bool = False,
) -> FastAPI:
    settings = settings or get_settings()
    state: dict = {
        "settings": settings,
        "query_service": query_service,
        "observer": None,
        "store": None,
    }

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if not skip_lifespan_index and state["query_service"] is None:
            store = IndexStore(settings)
            store.build_full()
            state["store"] = store
            state["query_service"] = QueryService(store, settings)
            state["observer"] = start_watcher(store)
        yield
        observer = state.get("observer")
        if observer is not None:
            observer.stop()
            observer.join(timeout=5)

    app = FastAPI(title="edges-rag", lifespan=lifespan)

    async def require_auth(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    ) -> None:
        verify_bearer(credentials, state["settings"].rag_api_token)

    @app.post("/ask", response_model=AskResponse)
    async def ask(
        body: AskRequest,
        _: None = Depends(require_auth),
    ) -> AskResponse:
        svc: QueryService = state["query_service"]
        return svc.ask(body.question)

    app.state.settings_ref = state  # type: ignore[attr-defined]
    return app


def _import_safe_app() -> FastAPI:
    """Module-level app for tooling. Real deploys use `python -m edges_rag`."""
    try:
        return create_app(skip_lifespan_index=True)
    except Exception:
        # Required env may be absent at import time (tests inject via create_app).
        return FastAPI(title="edges-rag")


# Import-safe default. Production entry `python -m edges_rag` builds the
# full index and starts the watcher (skip_lifespan_index=False).
app = _import_safe_app()
