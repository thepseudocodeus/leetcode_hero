# scripts/store.py
"""
Utilities for storing state

Notes:
"""

from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import json

from .mytypes import FileState

INDEX_FILE = Path("./index.parquet")
HASH_FILE = Path("./file_hashes.json")


def save_index(file_state: FileState) -> None:
    """Persist file state to disk (Parquet)."""
    df = pd.DataFrame(
        {
            "files": [str(f) for f in file_state.files],
            "dirs": [str(d) for d in file_state.dirs],
            "hashes": list(file_state.hashes.values()),
        }
    )
    pq.write_table(pa.Table.from_pandas(df), INDEX_FILE)


def load_index() -> FileState:
    """Load persisted index if available."""
    fs = FileState()
    if INDEX_FILE.exists():
        df = pq.read_table(INDEX_FILE).to_pandas()
        fs.files = [Path(f) for f in df["files"]]
        fs.dirs = [Path(d) for d in df["dirs"]]
        fs.hashes = dict(zip(fs.files, df["hashes"]))
    return fs


def save_hashes(hashes: dict) -> None:
    """Save file hashes to JSON for quick diff checking."""
    HASH_FILE.write_text(json.dumps(hashes, indent=2))


def load_hashes() -> dict:
    """Load previous file hashes."""
    if HASH_FILE.exists():
        return json.loads(HASH_FILE.read_text())
    return {}
