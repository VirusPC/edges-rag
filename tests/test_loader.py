from pathlib import Path

from edges_rag.loader import is_under_root, load_documents, should_index_file

ALLOW = [".md", ".py", ".txt"]
EXCLUDE = {"node_modules", ".git", "__pycache__", ".venv", "dist", "build"}


def test_should_index_respects_extension_and_exclude(tmp_path: Path):
    root = tmp_path
    good = root / "skills" / "x.md"
    good.parent.mkdir(parents=True)
    good.write_text("# hi", encoding="utf-8")
    assert should_index_file(good, root, ALLOW, EXCLUDE) is True

    bad_ext = root / "img.png"
    bad_ext.write_bytes(b"\x89PNG")
    assert should_index_file(bad_ext, root, ALLOW, EXCLUDE) is False

    skipped = root / "node_modules" / "pkg" / "a.md"
    skipped.parent.mkdir(parents=True)
    skipped.write_text("nope", encoding="utf-8")
    assert should_index_file(skipped, root, ALLOW, EXCLUDE) is False


def test_is_under_root_rejects_escape(tmp_path: Path):
    root = tmp_path / "edges"
    root.mkdir()
    outside = tmp_path / "other" / "x.md"
    outside.parent.mkdir()
    outside.write_text("x", encoding="utf-8")
    assert is_under_root(outside, root) is False
    assert is_under_root(root / "a.md", root) is True


def test_load_documents_sets_relative_path_metadata(tmp_path: Path):
    root = tmp_path
    f = root / "docs" / "a.md"
    f.parent.mkdir(parents=True)
    f.write_text("hello edges", encoding="utf-8")
    (root / "node_modules" / "x.md").parent.mkdir(parents=True)
    (root / "node_modules" / "x.md").write_text("skip", encoding="utf-8")
    (root / "bin.dat").write_bytes(b"\x00\x01\x02")

    docs = load_documents(root, ALLOW, EXCLUDE)
    assert len(docs) == 1
    assert docs[0].text == "hello edges"
    assert docs[0].metadata["path"] == "docs/a.md"
