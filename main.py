# file: ./main.py
# file: main.py
import subprocess
from pathlib import Path
from typing import Any, Callable

import typer
from InquirerPy import inquirer
from rich.console import Console
from rich.progress import track
from tdqm import tdqm

app = typer.Typer(help="🎮  LeetCode Hero: navigate your quests interactively.")
console = Console()


# def list_project_files() -> list[str]:
#     """Return a sorted list of all files in current project (excluding hidden)."""
#     base = Path(".")
#     return sorted(
#         str(p) for p in base.rglob("*") if p.is_file() and not p.name.startswith(".")
#     )


def list_project_files(base: Path = Path(".")) -> list[str]:
    """Return sorted file paths (excluding hidden)."""
    return sorted(
        str(p) for p in base.rglob("*") if p.is_file() and not p.name.startswith(".")
    )


# def process_with_progress(f: Callable, *args) -> Any:
#     output = []
#     n = len(args)
#     for i in tdqm(range(n), description=f"{f.__name__}..."):
#         tmp = f(*args[i])
#         output.append(tmp)
# return output


def process_with_progress(func: Callable[..., Any], items: list[Any]) -> list[Any]:
    """Run func on each item with a tqdm progress bar."""
    results = []
    for item in tqdm(items, desc=f"{func.__name__}"):
        results.append(func(item))
    return results


def process(f: Callable, *args) -> Any:
    console.rule(f"[bold cyan]🎮  {f.__name__}[/bold cyan]")
    result = process_with_progress(f, args)
    if result is not None:
        return result
    return None


def run_with_marimo(path: str) -> None:
    subprocess.run(["marimo", "run", path])


def open_in_vscode(path: str) -> None:
    subprocess.run(["code", path])


def print_contents(path: str) -> None:
    text = Path(path).read_text()
    console.rule(f"[green]{path}")
    console.print(text)


# @app.command()
# def run():
#     """Open the hero's console."""
#     console.rule("[bold cyan]📂  Choose your quest[/bold cyan]")
#     files = list_project_files()
#     if not files:
#         console.print("No files found.")
#         raise typer.Exit()

#     file_choice = inquirer.select(
#         message="Select a file:",
#         choices=files,
#         pointer="🗡️ ",
#         default=None,
#         vi_mode=True,
#     ).execute()

#     # choose an action
#     action = inquirer.select(
#         message=f"What do you want to do with '{file_choice}'?",
#         choices=[
#             "Run with marimo",
#             "Open in VSCode",
#             "Print contents",
#             "Cancel",
#         ],
#     ).execute()

#     if action == "Cancel":
#         console.print("[yellow]Quest abandoned.[/yellow]")
#         return

#     #  Use a rich progress bar
#     # for _ in track(range(3), description=f"{action}..."):
#     #     pass

#     if action == "Run with marimo":
#         subprocess.run(["marimo", "run", file_choice])
#     elif action == "Open in VSCode":
#         subprocess.run(["code", file_choice])
#     elif action == "Print contents":
#         text = Path(file_choice).read_text()
#         console.rule(f"[green]{file_choice}")
#         console.print(text)


@app.command()
def run() -> None:
    """Open the hero's console."""
    console.rule("[bold cyan]📂  Choose your quest[/bold cyan]")
    files = list_project_files()
    if not files:
        console.print("[red]No files found.[/red]")
        raise typer.Exit()

    file_choice = inquirer.select(
        message="Select a file:",
        choices=files,
        pointer="🗡️ ",
        vi_mode=True,
    ).execute()

    action = inquirer.select(
        message=f"What do you want to do with '{file_choice}'?",
        choices=["Run with marimo", "Open in VSCode", "Print contents", "Cancel"],
    ).execute()

    if action == "Cancel":
        console.print("[yellow]Quest abandoned.[/yellow]")
        return

    for _ in track(range(3), description=f"{action}..."):
        pass

    actions = {
        "Run with marimo": run_with_marimo,
        "Open in VSCode": open_in_vscode,
        "Print contents": print_contents,
    }
    func = actions.get(action)
    if func:
        func(file_choice)


if __name__ == "__main__":
    app()
