from __future__ import annotations

import os
import threading
from pathlib import Path

# Avoid Chroma's outbound telemetry during local persist.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from edges_rag.config import Settings
from edges_rag.loader import load_documents, should_index_file


class IndexStore:
    COLLECTION = "edges_rag"

    def __init__(
        self,
        settings: Settings,
        embed_model: BaseEmbedding | None = None,
    ) -> None:
        self.settings = settings
        self.settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        self._embed = embed_model or OllamaEmbedding(
            model_name=settings.ollama_embed_model,
            base_url=settings.ollama_base_url,
        )
        self._lock = threading.RLock()
        self._client = chromadb.PersistentClient(
            path=str(settings.chroma_persist_dir)
        )
        self._collection = self._open_collection()
        self._bind_index()

    def _open_collection(self):
        # LlamaIndex supplies embeddings; do not invoke Chroma's default ONNX model.
        return self._client.get_or_create_collection(
            name=self.COLLECTION,
            embedding_function=None,
        )

    def _bind_index(self) -> None:
        self._vector_store = ChromaVectorStore(chroma_collection=self._collection)
        self._storage_context = StorageContext.from_defaults(
            vector_store=self._vector_store
        )
        self._index = VectorStoreIndex.from_vector_store(
            self._vector_store,
            embed_model=self._embed,
            storage_context=self._storage_context,
        )

    def get_index(self) -> VectorStoreIndex:
        return self._index

    def build_full(self) -> int:
        with self._lock:
            try:
                self._client.delete_collection(self.COLLECTION)
            except Exception:
                pass
            self._collection = self._open_collection()
            self._bind_index()
            docs = load_documents(
                self.settings.index_root,
                self.settings.index_allow_extensions,
                self.settings.index_exclude_dirs,
            )
            for doc in docs:
                doc.doc_id = str(doc.metadata["path"])
            if docs:
                self._index = VectorStoreIndex.from_documents(
                    docs,
                    storage_context=self._storage_context,
                    embed_model=self._embed,
                )
            return len(docs)

    def _rel_path(self, path: Path) -> str:
        return path.resolve().relative_to(
            self.settings.index_root.resolve()
        ).as_posix()

    def upsert_file(self, path: Path) -> None:
        root = self.settings.index_root
        if not should_index_file(
            path,
            root,
            self.settings.index_allow_extensions,
            self.settings.index_exclude_dirs,
        ):
            return
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return
        rel = self._rel_path(path)
        with self._lock:
            self._delete_rel(rel)
            doc = Document(text=text, metadata={"path": rel})
            doc.doc_id = rel
            self._index.insert(doc)

    def delete_file(self, path: Path) -> None:
        try:
            rel = self._rel_path(path)
        except ValueError:
            # Watcher may report a path that no longer resolves under the root.
            rel = Path(path).as_posix()
        with self._lock:
            self._delete_rel(rel)

    def _delete_rel(self, rel: str) -> None:
        try:
            self._index.delete_ref_doc(rel, delete_from_docstore=True)
        except Exception:
            pass
        try:
            self._collection.delete(where={"path": rel})
        except Exception:
            pass

    def has_path(self, rel_path: str) -> bool:
        with self._lock:
            try:
                got = self._collection.get(where={"path": rel_path})
                ids = got.get("ids") or []
                return len(ids) > 0
            except Exception:
                return False
