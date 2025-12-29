# scripts/cli.py
"""
Interactive CLI for LeetCode Hero

Notes:
"""

import typer
from InquirerPy import inquirer
from rich.progress import track
from scripts.logic import (
    index_files,
    FileState,
    run_with_marimo,
    open_in_vscode,
    print_contents,
)
from scripts.models import CLIState

app = typer.Typer()
current_state = CLIState.INIT

# ----------------------------
# State Handling
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


def update_state(new_state: str):
    global current_state
    if new_state in ALLOWED_TRANSITIONS[current_state]:
        current_state = new_state
    else:
        print(f"Invalid transition: {current_state} → {new_state}")


# ----------------------------
# Menu
# ----------------------------
def main_menu():
    update_state(CLIState.MAIN_MENU)
    choices = {
        "Index / explore files": index_files,
        "Select a file to act on": file_selection_menu,
        "View logs": lambda: print(FileState),
        "Configure options": lambda: print("TBD"),
        "Quit": lambda: update_state(CLIState.EXIT),
    }

    choice = inquirer.select(
        message="Choose your quest:", choices=list(choices.keys()), pointer="🗡️ "
    ).execute()

    choices[choice]()
    if current_state != CLIState.EXIT:
        main_menu()


def file_selection_menu():
    update_state(CLIState.FILE_SELECTION)
    if not FileState["files"]:
        print("No files indexed! Run indexing first.")
        return

    file_choice = inquirer.select(
        message="Select a file:",
        choices=[str(f) for f in FileState["files"]],
        pointer="🗡️ ",
    ).execute()

    action_choice = inquirer.select(
        message=f"What do you want to do with '{file_choice}'?",
        choices=["Run with marimo", "Open in VSCode", "Print contents", "Cancel"],
    ).execute()

    if action_choice == "Cancel":
        return

    action_map = {
        "Run with marimo": run_with_marimo,
        "Open in VSCode": open_in_vscode,
        "Print contents": print_contents,
    }
    action_map[action_choice](file_choice)


# ----------------------------
# CLI Entrypoint
# ----------------------------
@app.command()
def run():
    update_state(CLIState.INIT)
    print("🎮 Welcome to LeetCode Hero!")
    main_menu()
