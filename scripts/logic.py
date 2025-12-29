# scripts/logic.py
"""
Utilities for CLI

Inspired by Knuth Literate Programming reading.

Notes:
"""

from hashlib import sha256
from pathlib import Path
from typing import Generator, Iterator

from tqdm import tqdm

from .mytypes import FileState
from .store import load_hashes, save_hashes, save_index

FILE_STATE = FileState()


def hash_file(path: Path) -> str:
    h = sha256()
    if path.is_dir():
        return ""
    h.update(path.read_bytes())
    return h.hexdigest()


def validate_files(input: Iterator[Path]) -> Generator[Path, None, None]:
    exclude_ext = [".md", ".ipynb", ".py", ".toml", ".yaml"]
    for p in input:
        if p.is_file() and not p.name.startswith(".") and p.suffix not in exclude_ext:
            yield p


def validate_dirs(input: Iterator[Path]) -> Generator[Path, None, None]:
    exclude_dirs = [
        ".venv",
        "venv",
        "git",
        ".git",
        "node_modules",
        ".node_modules",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    ]
    for d in input:
        if d.is_dir() and not d.name.startswith(".") and d.name not in exclude_dirs:
            yield d


def only_valid(input: Iterator[Path]) -> Generator[Path, None, None]:
    for e in input:
        if e.is_file() or e.is_dir():
            yield e


def list_project_files(base: Path = Path(".")) -> list[Path]:
    """Return all non-hidden files."""
    return sorted(p for p in only_valid(base.rglob("*")))


def build_index(force: bool = False) -> list[Path]:
    """Compute hash diff; only update changed files."""
    prev_hashes = load_hashes()
    files = list_project_files()
    changed = []

    for f in tqdm(files, desc="Indexing files"):
        new_hash = hash_file(f)
        if prev_hashes.get(str(f)) != new_hash:
            prev_hashes[str(f)] = new_hash
            changed.append(f)

    FILE_STATE.files = files
    FILE_STATE.dirs = sorted({p.parent for p in files})
    FILE_STATE.hashes = prev_hashes

    if changed or force:
        save_index(FILE_STATE)
        save_hashes(prev_hashes)

    return changed
