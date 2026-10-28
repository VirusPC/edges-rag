from __future__ import annotations

from llama_index.core.llms import LLM
from llama_index.llms.ollama import Ollama

from edges_rag.config import Settings
from edges_rag.index_store import IndexStore
from edges_rag.schemas import AskResponse, Citation

_SNIPPET_MAX = 240


def _snippet(text: str) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= _SNIPPET_MAX:
        return cleaned
    return cleaned[: _SNIPPET_MAX - 1] + "…"


class QueryService:
    def __init__(
        self,
        store: IndexStore,
        settings: Settings,
        llm: LLM | None = None,
    ) -> None:
        self.store = store
        self.settings = settings
        self.llm = llm or Ollama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
            request_timeout=120.0,
        )

    def ask(self, question: str) -> AskResponse:
        retriever = self.store.get_index().as_retriever(
            similarity_top_k=self.settings.rag_top_k
        )
        nodes = retriever.retrieve(question)
        citations: list[Citation] = []
        context_parts: list[str] = []
        for node in nodes:
            path = str(node.node.metadata.get("path", ""))
            text = node.node.get_content()
            score = getattr(node, "score", None)
            citations.append(
                Citation(
                    path=path,
                    snippet=_snippet(text),
                    score=float(score) if score is not None else None,
                )
            )
            context_parts.append(f"[{path}]\n{text}")
        context = "\n\n".join(context_parts) if context_parts else "(no context)"
        prompt = (
            "You are the Edges framework knowledge assistant. "
            "Answer using only the provided context. "
            "If the context is insufficient, say you do not know.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )
        completion = self.llm.complete(prompt)
        answer = str(completion.text).strip()
        return AskResponse(answer=answer, citations=citations)
