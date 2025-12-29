# scripts/store.py
"""
🎮 LeetCode Hero: Story-driven Interactive CLI
Utilities for storing state using Polars with quantitative metrics.

- [ ] TODO: is there a way to confirm with a dry run prior to executing?
"""

import json
from itertools import islice, zip_longest
from pathlib import Path

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from .mytypes import FileState
from ._store_polars import save_index_safe, compute_lazy_metrics

INDEX_FILE = Path("./index.parquet")
HASH_FILE = Path("./file_hashes.json")
METRICS_FILE = Path("./index_metrics.json")


def _chunked(iterable, size=10000):
    """Yield successive chunks from iterable."""
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk


def preflight_index(file_state: FileState, chunk_size: int = 1000):
    """
    Simulate save_index to detect potential errors without writing.
    Returns: success (bool), message (str), chunk_index (int or None)
    """
    rows_gen = zip_longest(
        file_state.files, file_state.dirs, file_state.hashes.values(), fillvalue=None
    )

    for i, chunk in enumerate(_chunked(rows_gen, chunk_size)):
        try:
            pl.DataFrame(chunk, schema=["files", "dirs", "hashes"])
        except Exception as e:
            return False, f"Chunk {i} failed: {e}", i

    return True, "All chunks passed preflight.", None


def sanitize(input: FileState) -> FileState:
    fs = [str(f) for f in input.files]
    ds = [str(d) for d in input.dirs]
    input.files = fs
    input.dirs = ds
    return input


def save_index(file_state: FileState) -> None:
    """Persist file state to disk (Parquet). Delegates to submodule."""
    save_index_safe(file_state, parquet_path=INDEX_FILE)


# def save_index(
#     file_state: FileState, chunk_size: int = 10000, preflight: bool = True
# ) -> None:
#     """
#     Persist file state incrementally using PyArrow.
#     Optionally run preflight to catch errors before writing.
#     """
#     # get rid of annoying type conversion issues
#     file_state = sanitize(file_state)
#     if preflight:
#         ok, msg, chunk = preflight_index(file_state, chunk_size)
#         if not ok:
#             raise ValueError(f"Preflight failed at chunk {chunk}: {msg}")
#         else:
#             print("Preflight check passed — proceeding to save.")

#     rows_gen = zip_longest(
#         file_state.files, file_state.dirs, file_state.hashes.values(), fillvalue=None
#     )

#     # - [ ] TODO: add a data converter for arrow here

#     # PyArrow chunked write
#     writer = None
#     for chunk in _chunked(rows_gen, chunk_size):
#         df_chunk = pl.DataFrame(chunk, schema=["files", "dirs", "hashes"])
#         # df_chunk = df_chunk.with_columns(
#         #     [
#         #         pl.col("files").apply(lambda x: str(x) if x is not None else None),
#         #         pl.col("dirs").apply(lambda x: str(x) if x is not None else None),
#         #     ]
#         # )
#         # switched to utf-8 to avoid polars type mismatches
#         df_chunk = df_chunk.with_columns(
#             [
#                 pl.col("files").cast(pl.Utf8),
#                 pl.col("dirs").cast(pl.Utf8),
#             ]
#         )
#         # table = pa.Table.from_pandas(df_chunk.to_pandas())
#         table = pa.Table.from_pandas(
#             df_chunk.to_pandas(),
#             schema=pa.schema(
#                 [("files", pa.string()), ("dirs", pa.string()), ("hashes", pa.string())]
#             ),
#         )
#         if writer is None:
#             writer = pq.ParquetWriter(INDEX_FILE, table.schema, compression="ZSTD")
#         writer.write_table(table)
#     if writer:
#         writer.close()

#     # Polars lazy read
#     df_lazy = pl.scan_parquet(INDEX_FILE)

#     metrics = {}
#     metrics["num_files"] = df_lazy.select(
#         pl.col("files").drop_nulls().count()
#     ).collect()[0, 0]
#     metrics["num_dirs"] = df_lazy.select(
#         pl.col("dirs").drop_nulls().n_unique()
#     ).collect()[0, 0]
#     metrics["num_hashes"] = df_lazy.select(
#         pl.col("hashes").drop_nulls().count()
#     ).collect()[0, 0]

#     # Files-per-dir statistics
#     if metrics["num_dirs"] > 0:
#         fpd = df_lazy.groupby("dirs").agg(pl.count("files").alias("files_per_dir"))[
#             "files_per_dir"
#         ]
#         fpd_metrics = (
#             fpd.select(
#                 [
#                     pl.col("files_per_dir").mean(),
#                     pl.col("files_per_dir").median(),
#                     pl.col("files_per_dir").std(),
#                     pl.col("files_per_dir").min(),
#                     pl.col("files_per_dir").max(),
#                     pl.col("files_per_dir").skew(),
#                     pl.col("files_per_dir").kurtosis(),
#                 ]
#             )
#             .collect()[0]
#             .to_dict()
#         )
#         metrics.update({f"files_per_dir_{k}": v for k, v in fpd_metrics.items()})

#     # Hash length statistics
#     hash_len = df_lazy.select(pl.col("hashes").str.lengths().alias("hash_length"))[
#         "hash_length"
#     ]
#     hash_metrics = (
#         hash_len.select(
#             [
#                 pl.col("hash_length").mean(),
#                 pl.col("hash_length").median(),
#                 pl.col("hash_length").std(),
#                 pl.col("hash_length").min(),
#                 pl.col("hash_length").max(),
#                 pl.col("hash_length").skew(),
#                 pl.col("hash_length").kurtosis(),
#             ]
#         )
#         .collect()[0]
#         .to_dict()
#     )
#     metrics.update({f"hash_length_{k}": v for k, v in hash_metrics.items()})

#     # Save metrics
#     METRICS_FILE.write_text(json.dumps(metrics, indent=2))


def load_index() -> FileState:
    """Load persisted index if available."""
    fs = FileState()
    if INDEX_FILE.exists():
        table = pq.read_table(INDEX_FILE)
        df = table.to_pandas()
        fs.files = [Path(f) for f in df["files"]]
        fs.dirs = [Path(d) for d in df["dirs"]]
        fs.hashes = dict(zip(fs.files, df["hashes"]))
    return fs


# def load_index() -> FileState:
#     """Load persisted index safely."""
#     fs = FileState()
#     if INDEX_FILE.exists():
#         df = pl.read_parquet(INDEX_FILE)
#         fs.files = [Path(f) for f in df["files"].to_list()]
#         fs.dirs = [Path(d) for d in df["dirs"].to_list()]
#         fs.hashes = dict(zip(fs.files, df["hashes"].to_list()))
#     return fs


def compute_metrics(file_state: FileState) -> dict:
    """Compute lazy metrics for the file state."""
    return compute_lazy_metrics(file_state)


def load_metrics() -> dict:
    """Load previously computed metrics."""
    if METRICS_FILE.exists():
        return json.loads(METRICS_FILE.read_text())
    return {}


def save_hashes(hashes: dict) -> None:
    """Save file hashes to JSON."""
    HASH_FILE.write_text(json.dumps(hashes, indent=2))


def load_hashes() -> dict:
    """Load previous file hashes."""
    if HASH_FILE.exists():
        return json.loads(HASH_FILE.read_text())
    return {}
