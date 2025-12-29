# scripts/cli.py
"""
🎮 LeetCode Hero: Story-driven Interactive CLI

This CLI orchestrates the user's journey:
- Navigate quests (indexing, selecting, and running files)
- Maintain FSM transitions
- Provide a playful, story-driven UX
"""

import typer
from InquirerPy import inquirer
from rich.console import Console

# Logic + data handling
from scripts.logic import (
    build_index,
    FILE_STATE,
)
from .do import (
    print_contents,
    open_in_vscode,
    run_with_marimo,
)
from scripts.mytypes import CLIState

app = typer.Typer(help="🎮  LeetCode Hero: interactive project explorer")
console = Console()

# ----------------------------
# Finite State Machine (FSM)
# ----------------------------
current_state = CLIState.INIT

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
    CLIState.ACTION_SELECTION: [CLIState.EXECUTION, CLIState.MAIN_MENU],
    CLIState.EXECUTION: [CLIState.MAIN_MENU],
    CLIState.VIEW_LOGS: [CLIState.MAIN_MENU],
    CLIState.CONFIGURE: [CLIState.MAIN_MENU],
    CLIState.EXIT: [],
}


def update_state(new_state: CLIState):
    """Transition to a new FSM state, enforcing allowed transitions."""
    global current_state
    if new_state in ALLOWED_TRANSITIONS[current_state]:
        current_state = new_state
        console.print(f"[cyan]→ State changed to {current_state}[/cyan]")
    else:
        console.print(f"[red]Invalid transition: {current_state} → {new_state}[/red]")


# ----------------------------
# Menu actions
# ----------------------------
def menu_index_files():
    """Index project files."""
    update_state(CLIState.INDEXING)
    console.rule("[bold cyan]📦 Indexing Project Files[/bold cyan]")

    changed = build_index(force=False)
    if changed:
        console.print(f"[green]Indexed {len(changed)} new or changed files.[/green]")
    else:
        console.print("[yellow]Index is already up-to-date![/yellow]")

    # update_state(CLIState.INDEXING)


def menu_file_selection():
    """Select a file and perform an action."""
    update_state(CLIState.FILE_SELECTION)

    if not FILE_STATE.files:
        console.print("[red]No files indexed! Run indexing first.[/red]")
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
        console.print("[yellow]Quest abandoned.[/yellow]")
        return

    action_map = {
        "Run with marimo": run_with_marimo,
        "Open in VSCode": open_in_vscode,
        "Print contents": print_contents,
    }

    update_state(CLIState.EXECUTION)
    func = action_map[action_choice]
    func(file_choice)
    update_state(CLIState.MAIN_MENU)


# ----------------------------
# Main Menu
# ----------------------------
def main_menu():
    """Display the main menu and handle navigation."""
    update_state(CLIState.MAIN_MENU)
    choices = {
        "Index / explore files": menu_index_files,
        "Select a file to act on": menu_file_selection,
        "View logs": lambda: console.print(FILE_STATE),
        "Configure options": lambda: console.print(
            "[yellow]Configuration TBD[/yellow]"
        ),
        "Quit": lambda: update_state(CLIState.EXIT),
    }

    choice = inquirer.select(
        message="Choose your quest:",
        choices=list(choices.keys()),
        pointer="🗡️ ",
    ).execute()

    action = choices[choice]
    action()

    if current_state != CLIState.EXIT:
        main_menu()


# ----------------------------
# CLI Entrypoint
# ----------------------------
@app.command()
def run():
    update_state(CLIState.INIT)
    console.rule("[bold magenta]🎮 Welcome to LeetCode Hero![/bold magenta]")
    main_menu()


if __name__ == "__main__":
    app()
