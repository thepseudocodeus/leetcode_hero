# scripts/store.py
"""
Utilities for storing state

Notes:
"""

from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from types import FileState

INDEX_FILE = Path("./index.parquet")


def save_index(file_state: FileState):
    df = pd.DataFrame(
        {
            "files": [str(f) for f in file_state.files],
            "dirs": [str(d) for d in file_state.dirs],
            "hashes": [h for h in file_state.hashes.values()],
        }
    )
    table = pa.Table.from_pandas(df)
    pq.write_table(table, INDEX_FILE)


def load_index() -> FileState:
    fs = FileState()
    if INDEX_FILE.exists():
        table = pq.read_table(INDEX_FILE)
        df = table.to_pandas()
        fs.files = [Path(f) for f in df["files"]]
        fs.dirs = [Path(d) for d in df["dirs"]]
        fs.hashes = dict(zip(fs.files, df["hashes"]))
    return fs
