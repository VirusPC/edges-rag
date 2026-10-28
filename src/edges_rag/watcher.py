from __future__ import annotations

from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from edges_rag.index_store import IndexStore


class IndexEventHandler(FileSystemEventHandler):
    def __init__(self, store: IndexStore) -> None:
        super().__init__()
        self.store = store

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self.store.upsert_file(Path(str(event.src_path)))

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self.store.upsert_file(Path(str(event.src_path)))

    def on_deleted(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self.store.delete_file(Path(str(event.src_path)))

    def on_moved(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self.store.delete_file(Path(str(event.src_path)))
        dest = getattr(event, "dest_path", None)
        if dest:
            self.store.upsert_file(Path(str(dest)))


def start_watcher(store: IndexStore) -> Observer:
    handler = IndexEventHandler(store)
    observer = Observer()
    root = store.settings.index_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    observer.schedule(handler, str(root), recursive=True)
    observer.start()
    return observer
