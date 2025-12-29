# scripts/_store_polars.py
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path


# -----------------------------
# Preflight & normalization
# -----------------------------
# def normalize_file_state(file_state):
#     """Ensure all paths are strings and hashes are aligned."""
#     all_files = [str(f) for f in file_state.files]
#     dirs_set = set(str(d) for d in file_state.dirs if d is not None)

#     files = [f for f in all_files if f not in dirs_set]

#     hashes = [file_state.hashes.get(f, "") for f in files]
#     dirs = list(dirs_set)

#     if not (len(files) == len(dirs) == len(hashes)):
#         raise ValueError("Files, dirs, and hashes must have the same length")

#     return files, dirs, hashes

def normalize_file_state(file_state):
    """Ensure all paths are strings and create file-to-dir mappings."""
    # Convert to strings
    all_files = [str(f) for f in file_state.files]
    dirs_set = set(str(d) for d in file_state.dirs if d is not None)

    # Filter to actual files only
    files = [f for f in all_files if f not in dirs_set]

    # Get parent directory for each file
    file_dirs = [str(Path(f).parent) for f in files]

    # Get hashes for actual files
    hashes = [file_state.hashes.get(f, "") for f in files]

    if not (len(files) == len(file_dirs) == len(hashes)):
        raise ValueError(f"Mismatch: {len(files)} files, {len(file_dirs)} dirs, {len(hashes)} hashes")

    return files, file_dirs, hashes


# -----------------------------
# Chunked Parquet write
# -----------------------------
def save_index_safe(file_state, parquet_path="index.parquet", chunk_size=5000):
    files, dirs, hashes = normalize_file_state(file_state)
    schema = pa.schema(
        [("files", pa.string()), ("dirs", pa.string()), ("hashes", pa.string())]
    )

    # Write in chunks to avoid memory spikes
    with pq.ParquetWriter(parquet_path, schema) as writer:
        for start in range(0, len(files), chunk_size):
            end = start + chunk_size
            table = pa.Table.from_arrays(
                [
                    pa.array(files[start:end], type=pa.string()),
                    pa.array(dirs[start:end], type=pa.string()),
                    pa.array(hashes[start:end], type=pa.string()),
                ],
                schema=schema,
            )
            writer.write_table(table)


# -----------------------------
# Lazy Polars metrics
# -----------------------------
def compute_lazy_metrics(file_state):
    files, dirs, hashes = normalize_file_state(file_state)

    df = pl.DataFrame({"files": files, "dirs": dirs, "hashes": hashes}).lazy()

    metrics = {}

    # Basic counts
    metrics["num_files"] = df.select(pl.count("files")).collect()[0, 0]
    metrics["num_dirs"] = df.select(pl.count("dirs")).collect()[0, 0]
    metrics["num_hashes"] = df.select(pl.count("hashes")).collect()[0, 0]

    # Files per dir
    if metrics["num_dirs"] > 0:
        fpd = df.groupby("dirs").agg(pl.count("files").alias("files_per_dir"))
        metrics["files_per_dir"] = {
            row["dirs"]: row["files_per_dir"] for row in fpd.collect().to_dicts()
        }

    hash_lengths = df.select(pl.col("hashes").apply(lambda x: len(x))).to_series()
    metrics["hash_length_mean"] = hash_lengths.mean()
    metrics["hash_length_std"] = hash_lengths.std()
    metrics["hash_length_min"] = hash_lengths.min()
    metrics["hash_length_max"] = hash_lengths.max()

    return metrics
