from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_EXTS = (
    ".md,.txt,.py,.ts,.tsx,.js,.jsx,.json,.yaml,.yml,.toml,.sh,.rs,.go"
)
_DEFAULT_EXCLUDE = "node_modules,.git,__pycache__,.venv,dist,build"


def parse_extensions(raw: str) -> list[str]:
    out: list[str] = []
    for part in raw.split(","):
        p = part.strip().lower()
        if not p:
            continue
        if not p.startswith("."):
            p = f".{p}"
        out.append(p)
    return out


def parse_exclude_dirs(raw: str) -> set[str]:
    return {p.strip() for p in raw.split(",") if p.strip()}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    index_root: Path = Field(alias="INDEX_ROOT")
    edges_root: Path | None = Field(default=None, alias="EDGES_ROOT")
    chroma_persist_dir: Path = Field(alias="CHROMA_PERSIST_DIR")
    ollama_base_url: str = Field(alias="OLLAMA_BASE_URL")
    ollama_embed_model: str = Field(alias="OLLAMA_EMBED_MODEL")
    ollama_chat_model: str = Field(alias="OLLAMA_CHAT_MODEL")
    rag_api_token: str = Field(alias="RAG_API_TOKEN")
    rag_top_k: int = Field(default=5, alias="RAG_TOP_K")
    rag_host: str = Field(default="0.0.0.0", alias="RAG_HOST")
    rag_port: int = Field(default=8000, alias="RAG_PORT")
    index_allow_extensions_raw: str = Field(
        default=_DEFAULT_EXTS, alias="INDEX_ALLOW_EXTENSIONS"
    )
    index_exclude_dirs_raw: str = Field(
        default=_DEFAULT_EXCLUDE, alias="INDEX_EXCLUDE_DIRS"
    )

    @property
    def index_allow_extensions(self) -> list[str]:
        return parse_extensions(self.index_allow_extensions_raw)

    @property
    def index_exclude_dirs(self) -> set[str]:
        return parse_exclude_dirs(self.index_exclude_dirs_raw)

    @field_validator("index_root", "chroma_persist_dir", "edges_root", mode="before")
    @classmethod
    def _pathify(cls, v: object) -> object:
        if isinstance(v, str):
            if v == "":
                return None
            return Path(v)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
