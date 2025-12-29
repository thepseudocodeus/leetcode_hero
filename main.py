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
import subprocess
from pathlib import Path
from typing import Generator, Iterator, List

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import typer
from InquirerPy import inquirer
from rich.console import Console
from tqdm import tqdm

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
# Use of lists reduces complexity of conditional approach used previously
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
    CLIState.ACTION_SELECTION: [
        CLIState.EXECUTION,
        CLIState.FILE_SELECTION,
        CLIState.MAIN_MENU,
    ],
    CLIState.EXECUTION: [CLIState.MAIN_MENU],
    CLIState.VIEW_LOGS: [CLIState.MAIN_MENU],
    CLIState.CONFIGURE: [CLIState.MAIN_MENU],
    CLIState.EXIT: [],
}

current_state = CLIState.INIT


# Single source of state truth - should only allow valid states
# - [ ] TODO: use math to validate by generating random states using monte carlo
def update_state(new_state: str):
    global current_state
    if new_state in ALLOWED_TRANSITIONS[current_state]:
        current_state = new_state
        console.print(f"[bold cyan]State updated → {current_state}[/bold cyan]")
    else:
        console.print(f"[red]Invalid transition: {current_state} → {new_state}[/red]")


# ----------------------------
# Model / File Indexing
# ----------------------------
# - [ ] TODO: annotate using typing for mypy
FILE_STATE = {
    "files": [],
    "dirs": [],
    "hashes": {},
}


def hash_file(path: Path) -> str:
    """Return SHA256 hash of file contents."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def validate_files(input: Iterator[Path]) -> Generator[Path, None, None]:
    """Filter out non-files and hidden files."""
    for i in tdqm(input, desc="Validating files"):
        if i.is_file() and not i.name.startswith("."):
            yield i


def list_project_files(base: Path = Path(".")) -> List[Path]:
    """Return all files in the project (non-hidden)."""
    exclude = [".toml", ".md"]
    return sorted(p for p in validate_files(base.rglob("*")) if p.suffix not in exclude)


def index_files(force: bool = False):
    """Index files only if new or changed."""
    update_state(CLIState.INDEXING)
    files = list_project_files()
    updated = False

    for f in tqdm(files, desc="Indexing files"):
        file_hash = hash_file(f)
        if f not in FILE_STATE["hashes"] or FILE_STATE["hashes"][f] != file_hash:
            FILE_STATE["hashes"][f] = file_hash
            updated = True

    FILE_STATE["files"] = files
    FILE_STATE["dirs"] = sorted(set(p.parent for p in files))

    if updated or force:
        table = pa.Table.from_pandas(pd.DataFrame(FILE_STATE))
        pq.write_table(table, INDEX_FILE)
        console.print(f"[green]Index updated with {len(files)} files.[/green]")
    else:
        console.print("[yellow]Index is up-to-date.[/yellow]")


# ----------------------------
# Action functions
# ----------------------------
def run_with_marimo(path: str):
    subprocess.run(["marimo", "run", path])


def open_in_vscode(path: str):
    subprocess.run(["code", path])


def print_contents(path: str):
    text = Path(path).read_text()
    console.rule(f"[green]{path}")
    console.print(text)


# ----------------------------
# View / Menu
# ----------------------------
def main_menu():
    update_state(CLIState.MAIN_MENU)
    choices = {
        "Index / explore files": index_files,
        "Select a file to act on": file_selection_menu,
        "View logs": lambda: console.print(FILE_STATE),
        "Configure options": lambda: console.print("Configuration TBD"),
        "Quit": lambda: update_state(CLIState.EXIT),
    }

    choice = inquirer.select(
        message="Choose your quest:", choices=list(choices.keys()), pointer="🗡️ "
    ).execute()

    action = choices[choice]
    action()
    if current_state != CLIState.EXIT:
        main_menu()  # Loop back to main menu


def file_selection_menu():
    update_state(CLIState.FILE_SELECTION)
    if not FILE_STATE["files"]:
        console.print("[red]No files indexed! Run indexing first.[/red]")
        return

    file_choice = inquirer.select(
        message="Select a file:",
        choices=[str(f) for f in FILE_STATE["files"]],
        pointer="🗡️ ",
    ).execute()

    update_state(CLIState.ACTION_SELECTION)
    action_choice = inquirer.select(
        message=f"What do you want to do with '{file_choice}'?",
        choices=["Run with marimo", "Open in VSCode", "Print contents", "Cancel"],
        pointer="🗡️ ",
    ).execute()

    if action_choice == "Cancel":
        console.print("[yellow]Quest abandoned.[/yellow]")
        return

    action_map = {
        "Run with marimo": run_with_marimo,
        "Open in VSCode": open_in_vscode,
        "Print contents": print_contents,
    }

    update_state(CLIState.EXECUTION)
    action_map[action_choice](file_choice)


# ----------------------------
# CLI entrypoint
# ----------------------------
@app.command()
def run():
    update_state(CLIState.INIT)
    console.print("[bold cyan]🎮 Welcome to LeetCode Hero![/bold cyan]")
    main_menu()


if __name__ == "__main__":
    app()
