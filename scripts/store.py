# scripts/store.py
"""
Utilities for storing state

Notes:
"""
# scripts/store.py
"""
Utilities for storing state using Polars with quantitative metrics.
"""

import json
from itertools import zip_longest
from pathlib import Path

import polars as pl

from .mytypes import FileState

INDEX_FILE = Path("./index.parquet")
HASH_FILE = Path("./file_hashes.json")
METRICS_FILE = Path("./index_metrics.json")


def save_index(file_state: FileState, chunk_size: int = 10000) -> None:
    """Persist file state to disk efficiently and compute top-tier metrics."""
    # Validate inputs
    files_len = len(file_state.files)
    dirs_len = len(file_state.dirs)
    hashes_len = len(file_state.hashes)
    max_len = max(files_len, dirs_len, hashes_len)
    min_len = min(files_len, dirs_len, hashes_len)
    if max_len / max(1, min_len) > 10:
        print(f"⚠️ Warning: input lengths differ significantly: {files_len}, {dirs_len}, {hashes_len}")

    # Row-wise combination using generator
    rows_gen = zip_longest(file_state.files, file_state.dirs, file_state.hashes.values(), fillvalue=None)

    # Chunked, memory-efficient Polars DataFrame
    df = pl.from_records(rows_gen, schema=["files", "dirs", "hashes"], chunk_size=chunk_size)

    # Persist to Parquet (multi-threaded)
    df.write_parquet(INDEX_FILE, use_pyarrow=True)

    # --- Compute expert-level metrics ---
    metrics = {}

    # General counts
    metrics["num_files"] = df["files"].drop_nulls().count()
    metrics["num_dirs"] = df["dirs"].drop_nulls().unique().count()
    metrics["num_hashes"] = df["hashes"].drop_nulls().count()

    # File-per-dir distribution
    if metrics["num_dirs"] > 0:
        fpd = df.groupby("dirs").agg(pl.count("files").alias("files_per_dir"))["files_per_dir"]
        metrics.update({
            "files_per_dir_mean": fpd.mean(),
            "files_per_dir_median": fpd.median(),
            "files_per_dir_std": fpd.std(),
            "files_per_dir_min": fpd.min(),
            "files_per_dir_max": fpd.max(),
            "files_per_dir_skew": fpd.skew(),
            "files_per_dir_kurtosis": fpd.kurtosis(),
        })

    # Hash-length statistics
    hash_lengths = df["hashes"].str.lengths()
    metrics.update({
        "hash_length_mean": hash_lengths.mean(),
        "hash_length_median": hash_lengths.median(),
        "hash_length_std": hash_lengths.std(),
        "hash_length_min": hash_lengths.min(),
        "hash_length_max": hash_lengths.max(),
        "hash_length_skew": hash_lengths.skew(),
        "hash_length_kurtosis": hash_lengths.kurtosis(),
    })

    # Save metrics as JSON
    METRICS_FILE.write_text(json.dumps(metrics, indent=2))


def load_index() -> FileState:
    """Load persisted index."""
    fs = FileState()
    if INDEX_FILE.exists():
        df = pl.read_parquet(INDEX_FILE)
        fs.files = [Path(f) for f in df["files"].to_list()]
        fs.dirs = [Path(d) for d in df["dirs"].to_list()]
        fs.hashes = dict(zip(fs.files, df["hashes"].to_list()))
    return fs


def load_metrics() -> dict:
    """Load previously computed metrics, if any."""
    if METRICS_FILE.exists():
        return json.loads(METRICS_FILE.read_text())
    return {}


def save_hashes(hashes: dict) -> None:
    """Save file hashes to JSON for quick diff checking."""
    HASH_FILE.write_text(json.dumps(hashes, indent=2))


def load_hashes() -> dict:
    """Load previous file hashes."""
    if HASH_FILE.exists():
        return json.loads(HASH_FILE.read_text())
    return {}
