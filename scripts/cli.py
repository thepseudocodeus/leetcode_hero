# scripts/cli.py
"""
Interactive CLI for LeetCode Hero

Notes:
"""
import typer
from InquirerPy import inquirer
from rich.progress import track

from core import FILE_STATE, update_state, current_state, list_project_files
from persistence import save_index
from actions import run_with_marimo, open_in_vscode, print_contents
from types import CLIState

app = typer.Typer(help="🎮  LeetCode Hero: interactive CLI")


def main_menu():
    update_state(CLIState.MAIN_MENU)
    choices = {
        "Index / explore files": index_files,
        "Select a file to act on": file_selection_menu,
        "View logs": lambda: print(FILE_STATE),
        "Configure options": lambda: print("Configuration TBD"),
        "Quit": lambda: update_state(CLIState.EXIT),
    }

    choice = inquirer.select(
        message="Choose your quest:", choices=list(choices.keys()), pointer="🗡️ "
    ).execute()

    action = choices[choice]
    action()
    if current_state != CLIState.EXIT:
        main_menu()


def index_files(force: bool = False):
    update_state(CLIState.INDEXING)
    files = list_project_files()
    updated = False

    for f in files:
        file_hash = f"{f.stat().st_mtime}"  # simple change detection
        if f not in FILE_STATE.hashes or FILE_STATE.hashes[f] != file_hash:
            FILE_STATE.hashes[f] = file_hash
            updated = True

    FILE_STATE.files = files
    FILE_STATE.dirs = sorted(set(f.parent for f in files))

    if updated or force:
        save_index(FILE_STATE)


def file_selection_menu():
    update_state(CLIState.FILE_SELECTION)
    if not FILE_STATE.files:
        print("[red]No files indexed! Run indexing first.[/red]")
        return

    file_choice = inquirer.select(
        message="Select a file:",
        choices=[str(f) for f in FILE_STATE.files],
        pointer="🗡️ ",
    ).execute()

    update_state(CLIState.ACTION_SELECTION)
    action_choice = inquirer.select(
        message=f"What do you want to do with '{file_choice}'?",
        choices=["Run with marimo", "Open in VSCode", "Print contents", "Cancel"],
        pointer="🗡️ ",
    ).execute()

    if action_choice == "Cancel":
        return

    action_map = {
        "Run with marimo": run_with_marimo,
        "Open in VSCode": open_in_vscode,
        "Print contents": print_contents,
    }

    update_state(CLIState.EXECUTION)
    action_map[action_choice](file_choice)


@app.command()
def run():
    update_state(CLIState.INIT)
    print("[bold cyan]🎮 Welcome to LeetCode Hero![/bold cyan]")
    main_menu()


if __name__ == "__main__":
    app()
