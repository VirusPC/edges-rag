from __future__ import annotations

from pathlib import Path

from llama_index.core import Document


def is_under_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def should_index_file(
    path: Path,
    root: Path,
    allow_exts: list[str],
    exclude_dirs: set[str],
) -> bool:
    if not path.is_file():
        return False
    if path.is_symlink():
        # Reject symlinks that escape INDEX_ROOT after resolution.
        if not is_under_root(path, root):
            return False
    if not is_under_root(path, root):
        return False
    rel = path.resolve().relative_to(root.resolve())
    if any(part in exclude_dirs for part in rel.parts[:-1]):
        return False
    if path.suffix.lower() not in {ext.lower() for ext in allow_exts}:
        return False
    return True


def load_documents(
    root: Path,
    allow_exts: list[str],
    exclude_dirs: set[str],
) -> list[Document]:
    root = root.resolve()
    docs: list[Document] = []
    if not root.is_dir():
        return docs
    # Do not follow directory symlinks (pathlib rglob default).
    for path in root.rglob("*"):
        if path.is_symlink() and not is_under_root(path, root):
            continue
        if not should_index_file(path, root, allow_exts, exclude_dirs):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.resolve().relative_to(root).as_posix()
        docs.append(Document(text=text, metadata={"path": rel}))
    return docs
