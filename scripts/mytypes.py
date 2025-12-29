# scripts/types.py
"""
Types for CLI

Notes:
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List


class CLIState(str, Enum):
    INIT = "INIT"
    MAIN_MENU = "MAIN_MENU"
    INDEXING = "INDEXING"
    FILE_SELECTION = "FILE_SELECTION"
    ACTION_SELECTION = "ACTION_SELECTION"
    EXECUTION = "EXECUTION"
    VIEW_LOGS = "VIEW_LOGS"
    CONFIGURE = "CONFIGURE"
    EXIT = "EXIT"


@dataclass
class FileState:
    files: List[Path]
    dirs: List[Path]
    hashes: Dict[Path, str]

    def __init__(self):
        self.files = []
        self.dirs = []
        self.hashes = {}
