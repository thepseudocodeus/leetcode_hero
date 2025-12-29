# scripts/logic.py
"""
Utilities for CLI

Inspired by Knuth Literate Programming reading.

Notes:
"""

from pathlib import Path
from hashlib import sha256
from tqdm import tqdm

from .store import save_index, load_index, save_hashes, load_hashes
from .mytypes import FileState

FILE_STATE = FileState()


def hash_file(path: Path) -> str:
    h = sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def list_project_files(base: Path = Path(".")) -> list[Path]:
    """Return all non-hidden files."""
    return sorted(
        p for p in base.rglob("*") if p.is_file() and not p.name.startswith(".")
    )


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
