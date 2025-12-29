"""
Utilities for CLI

Inspired by Knuth Literate Programming reading.

Notes:
"""

import hashlib
from pathlib import Path
from types import CLIState, FileState
from typing import Callable, Generator, Iterator, List

from tqdm import tqdm

# Global state
current_state = CLIState.INIT
FILE_STATE = FileState()

# ----------------------------
# FSM / State management
# ----------------------------
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


def update_state(new_state: CLIState):
    """Update FSM state only if transition is allowed."""
    global current_state
    if new_state in ALLOWED_TRANSITIONS[current_state]:
        current_state = new_state
    else:
        raise ValueError(f"Invalid FSM transition: {current_state} -> {new_state}")


# ----------------------------
# File utilities
# ----------------------------
def hash_file(path: Path) -> str:
    """SHA256 hash for file contents."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def validate_files(input: Iterator[Path]) -> Generator[Path, None, None]:
    """Yield only files and non-hidden files."""
    for i in tqdm(input, desc="Validating files"):
        if i.is_file() and not i.name.startswith("."):
            yield i


def list_project_files(base: Path = Path("."), exclude: List[str] = None) -> List[Path]:
    """Return project files excluding certain suffixes."""
    exclude = exclude or [".toml", ".md"]
    return sorted(p for p in validate_files(base.rglob("*")) if p.suffix not in exclude)


def process_with_progress(func: Callable, items: list) -> list:
    """Run func on items with tqdm progress bar."""
    results = []
    for item in tqdm(items, desc=f"{func.__name__}"):
        results.append(func(item))
    return results
