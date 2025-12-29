"""
🎮 LeetCode Hero: Story-driven interactive CLI

This CLI allows the hero (you/dev) to explore the project realm,
select quests (problems we want to solve), and perform actions (run Marimo, open in VSCode, print contents) on objects (files, directories, etc).

Features:
- Smart indexing: only new/changed files are indexed.
- Persistent state: file hashes saved for fast future indexing.
- Progress feedback: tqdm shows live progress during indexing.
- Story-driven navigation: each function is a narrative chapter.

Notes:
- Draft of my story-driven development method inspired by Literate Programming (LP).
- Use of hashing inspired by Linux OS installation procedures where check downloaded hash against expected hash.
- Inspired by elm for this as well.
"""

# IMPORT & SETUP
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import typer
from InquirerPy import inquirer
from rich.console import Console
from rich.progress import track
from tqdm import tqdm

from typing import Any, Callable, List, Dict

# ----------------------------
# Setup
# ----------------------------
app = typer.Typer(help="🎮  LeetCode Hero: navigate your quests interactively.")
console = Console()
INDEX_FILE = Path("./index.parquet")
HASH_FILE = Path("./file_hashes.json")

# ----------------------------
# Finite State Machine
# ----------------------------
class CLIState:
    INIT = "INIT"
    MAIN_MENU = "MAIN_MENU"
    INDEXING = "INDEXING"
    FILE_SELECTION = "FILE_SELECTION"
    ACTION_SELECTION = "ACTION_SELECTION"
    EXECUTION = "EXECUTION"
    VIEW_LOGS = "VIEW_LOGS"
    CONFIGURE = "CONFIGURE"
    EXIT = "EXIT"

# Valid transitions: state -> list of allowed next states
ALLOWED_TRANSITIONS = {
    CLIState.INIT: [CLIState.MAIN_MENU, CLIState.EXIT],
    CLIState.MAIN_MENU: [
        CLIState.INDEXING,
        CLIState.FILE_SELECTION,
        CLIState.VIEW_LOGS,
        CLIState.CONFIGURE,
        CLIState.EXIT,
    ],
    CLIState.INDEXING: [CLIState.MAIN_MENU],
    CLIState.FILE_SELECTION: [CLIState.ACTION_SELECTION, CLIState.MAIN_MENU],
    CLIState.ACTION_SELECTION: [CLIState.EXECUTION, CLIState.FILE_SELECTION, CLIState.MAIN_MENU],
    CLIState.EXECUTION: [CLIState.MAIN_MENU],
    CLIState.VIEW_LOGS: [CLIState.MAIN_MENU],
    CLIState.CONFIGURE: [CLIState.MAIN_MENU],
    CLIState.EXIT: [],
}

current_state = CLIState.INIT

def update_state(new_state: str):
    global current_state
    if new_state in ALLOWED_TRANSITIONS[current_state]:
        current_state = new_state
        console.print(f"[bold cyan]State updated → {current_state}[/bold cyan]")
    else:
        console.print(f"[red]Invalid transition: {current_state} → {new_state}[/red]")

# =============================
# Stage 1 – Helpers for indexing
# =============================

def hash_file(file_path: Path) -> str:
    """Compute SHA256 hash of a file to detect changes."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_hashes() -> dict[str, str]:
    """Load previously saved file hashes, or return empty dict."""
    if HASH_FILE.exists():
        return json.loads(HASH_FILE.read_text())
    return {}


def save_hashes(hashes: dict[str, str]):
    """Save file hashes for next run."""
    HASH_FILE.write_text(json.dumps(hashes, indent=2))


def list_project_files(base: Path = Path(".")) -> list[Path]:
    """Return sorted list of all project files, excluding hidden files."""
    return sorted([p for p in base.rglob("*") if p.is_file() and not p.name.startswith(".")])


def index_files(base: Path = Path("."), force: bool = False) -> list[Path]:
    """
    Index project files smartly:
    - Only new or changed files are included unless force=True
    - Saves updated hash state
    - Stores index as Parquet for persistent state
    """
    console.rule("[bold cyan]📦 Indexing the realm[/bold cyan]")
    files = list_project_files(base)
    previous_hashes = load_hashes()
    updated_hashes = {}
    indexed_files = []

    for f in tqdm(files, desc="Indexing files"):
        h = hash_file(f)
        updated_hashes[str(f)] = h
        if force or previous_hashes.get(str(f)) != h:
            indexed_files.append(f)

    save_hashes(updated_hashes)

    # Save to Parquet
    df = pd.DataFrame({"files": [str(f) for f in indexed_files]})
    table = pa.Table.from_pandas(df)
    pq.write_table(table, INDEX_FILE)
    return indexed_files


# =============================
# Stage 2 – Action functions
# =============================

def run_with_marimo(path: str) -> None:
    """Run a Python file using Marimo."""
    subprocess.run(["marimo", "run", path])


def open_in_vscode(path: str) -> None:
    """Open a file in VSCode."""
    subprocess.run(["code", path])


def print_contents(path: str) -> None:
    """Print file contents to the console."""
    text = Path(path).read_text()
    console.rule(f"[green]{path}")
    console.print(text)


# =============================
# Stage 3 – CLI interaction
# =============================

@app.command()
def run(force_index: bool = typer.Option(False, "--force", "-f", help="Force reindex all files")) -> None:
    """
    Open the hero's console:
    1. Smart indexing (only new/changed files unless --force)
    2. Select a file to perform a quest on
    3. Choose action: Marimo, VSCode, print contents
    """

    # Stage 1: Smart indexing
    files = index_files(force=force_index)
    if not files:
        console.print("[red]No files found to quest on.[/red]")
        raise typer.Exit()

    # Stage 2: File selection
    file_choice = inquirer.select(
        message="Select a file to quest on:",
        choices=[str(f) for f in files],
        pointer="🗡️ ",
        vi_mode=True,
    ).execute()

    # Stage 3: Choose action
    action = inquirer.select(
        message=f"What shall the hero do with '{file_choice}'?",
        choices=["Run with Marimo", "Open in VSCode", "Print contents", "Cancel"],
    ).execute()

    if action == "Cancel":
        console.print("[yellow]Quest abandoned.[/yellow]")
        return

    # Stage 4: Optional progress animation
    for _ in track(range(3), description=f"{action}..."):
        pass

    # Stage 5: Execute action
    actions = {
        "Run with Marimo": run_with_marimo,
        "Open in VSCode": open_in_vscode,
        "Print contents": print_contents,
    }
    func = actions.get(action)
    if func:
        func(file_choice)


# =============================
# Stage 4 – Entry point
# =============================

if __name__ == "__main__":
    app()
