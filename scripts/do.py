# scripts/actions.py
"""
Actions for CLI

Notes:
"""

import subprocess
from pathlib import Path
from rich.console import Console

console = Console()


def run_with_marimo(path: str):
    subprocess.run(["marimo", "run", path])


def open_in_vscode(path: str):
    subprocess.run(["code", path])


def print_contents(path: str):
    text = Path(path).read_text()
    console.rule(f"[green]{path}")
    console.print(text)
