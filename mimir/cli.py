"""CLI interface for Mimir."""
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from mimir.config import logger, settings
from mimir.db import db_manager
from mimir.models import Branch, ContextCommit, Task
from mimir.services.branch_service import BranchService
from mimir.services.commit_service import CommitService
from mimir.services.task_service import TaskService
from mimir.state_manager import StateManager

app = typer.Typer(help="Mimir - Cognitive Context Management System")
console = Console()


def get_services():
    """Helper to get services."""
    session = db_manager.get_session()
    return {
        "task_service": TaskService(session),
        "commit_service": CommitService(session),
        "branch_service": BranchService(session),
        "session": session,
    }


@app.command()
def init(
    database_url: Optional[str] = typer.Option(
        None,
        "--db-url",
        help="Database URL (or use DATABASE_URL env var)",
    ),
) -> None:
    """Initialize Mimir database."""
    try:
        url = database_url or settings.database_url
        console.print(f"[bold blue]Initializing database:[/bold blue] {url}")
        db_manager.init_db()
        console.print("[bold green]✓ Database initialized successfully[/bold green]")
    except Exception as e:
        console.print(f"[bold red]✗ Error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def create_task(
    name: str = typer.Argument(..., help="Task name (e.g., TASK-42)"),
    author: str = typer.Option("default", "--author", help="Task creator"),
) -> None:
    """Create a new task with main branch."""
    try:
        services = get_services()
        task = services["task_service"].create_task(name=name, author=author)
        services["session"].commit()
        services["session"].close()

        StateManager.set_current_task(name)

        console.print(f"[bold green]✓ Created task:[/bold green] {name}")
        console.print(f"  [dim]ID:[/dim] {task.id}")
        console.print(f"  [dim]Main branch created[/dim]")
    except ValueError as e:
        console.print(f"[bold red]✗ Error: {e}[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        logger.exception("Unexpected error in create_task")
        console.print(f"[bold red]✗ Unexpected error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def commit(
    task: Optional[str] = typer.Option(None, "--task", help="Task name"),
    branch: Optional[str] = typer.Option(None, "--branch", help="Branch name"),
    message: str = typer.Option(..., "--message", help="Commit message"),
    context_file: Optional[Path] = typer.Option(
        None, "--context-file", help="File with context content"
    ),
    context: Optional[str] = typer.Option(None, "--context", help="Inline context"),
    author: str = typer.Option("default", "--author", help="Commit author"),
    cognitive_load: Optional[int] = typer.Option(None, "--cognitive-load", help="Cognitive load (0-10)"),
    uncertainty: Optional[int] = typer.Option(None, "--uncertainty", help="Uncertainty (0-10)"),
) -> None:
    """Create a new commit on a branch."""
    try:
        # Resolve task and branch from current state if not provided
        task_name = task or StateManager.get_current_task()
        branch_name = branch or StateManager.get_current_branch() or "main"

        if not task_name:
            console.print("[bold red]✗ Error: Task not specified and no current task set[/bold red]")
            raise typer.Exit(1)

        # Get context
        if context_file:
            context_content = context_file.read_text()
        elif context:
            context_content = context
        else:
            console.print("[bold red]✗ Error: No context provided (--context or --context-file)[/bold red]")
            raise typer.Exit(1)

        services = get_services()
        
        # Get task ID
        task_obj = services["task_service"].get_task_by_name(task_name)
        if not task_obj:
            console.print(f"[bold red]✗ Error: Task '{task_name}' not found[/bold red]")
            raise typer.Exit(1)

        # Create commit
        new_commit = services["commit_service"].create_commit(
            task_id=task_obj.id,
            branch_name=branch_name,
            message=message,
            context=context_content,
            author=author,
            cognitive_load=cognitive_load,
            uncertainty=uncertainty,
        )
        services["session"].commit()
        services["session"].close()

        console.print(f"[bold green]✓ Created commit:[/bold green] {message}")
        console.print(f"  [dim]ID:[/dim] {new_commit.id}")
        console.print(f"  [dim]Branch:[/dim] {branch_name}")
        console.print(f"  [dim]Author:[/dim] {author}")
        if cognitive_load is not None:
            console.print(f"  [dim]Cognitive Load:[/dim] {cognitive_load}")
        if uncertainty is not None:
            console.print(f"  [dim]Uncertainty:[/dim] {uncertainty}")

    except ValueError as e:
        console.print(f"[bold red]✗ Error: {e}[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        logger.exception("Unexpected error in commit")
        console.print(f"[bold red]✗ Unexpected error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def branch(
    action: str = typer.Argument("list", help="Action: list, create, delete"),
    name: Optional[str] = typer.Argument(None, help="Branch name"),
    task: Optional[str] = typer.Option(None, "--task", help="Task name"),
    from_branch: Optional[str] = typer.Option(None, "--from", help="Create from branch"),
) -> None:
    """Manage branches."""
    try:
        task_name = task or StateManager.get_current_task()
        
        if not task_name and action != "list":
            console.print("[bold red]✗ Error: Task not specified[/bold red]")
            raise typer.Exit(1)

        services = get_services()

        if action == "list":
            # List branches
            if task_name:
                task_obj = services["task_service"].get_task_by_name(task_name)
                if not task_obj:
                    console.print(f"[bold red]✗ Error: Task '{task_name}' not found[/bold red]")
                    raise typer.Exit(1)
                branches = services["branch_service"].list_branches(task_obj.id)
                
                if branches:
                    table = Table(title=f"Branches for {task_name}")
                    table.add_column("Name", style="cyan")
                    table.add_column("Head Commit", style="green")
                    table.add_column("Created At", style="dim")
                    
                    for br in branches:
                        table.add_row(
                            br.name,
                            str(br.head_commit_id)[:8] if br.head_commit_id else "—",
                            br.created_at.isoformat()[:19],
                        )
                    console.print(table)
                else:
                    console.print("[dim]No branches found[/dim]")
            else:
                console.print("[bold yellow]ⓘ No task specified. Use --task to list branches.[/bold yellow]")

        elif action == "create":
            if not name:
                console.print("[bold red]✗ Error: Branch name required[/bold red]")
                raise typer.Exit(1)

            task_obj = services["task_service"].get_task_by_name(task_name)
            if not task_obj:
                console.print(f"[bold red]✗ Error: Task '{task_name}' not found[/bold red]")
                raise typer.Exit(1)

            # Get from commit
            from_commit_id = None
            if from_branch:
                from_br = services["branch_service"].get_branch(task_obj.id, from_branch)
                if not from_br:
                    console.print(f"[bold red]✗ Error: Branch '{from_branch}' not found[/bold red]")
                    raise typer.Exit(1)
                from_commit_id = from_br.head_commit_id

            new_branch = services["branch_service"].create_branch(
                task_id=task_obj.id,
                name=name,
                from_commit_id=from_commit_id,
            )
            services["session"].commit()
            services["session"].close()

            console.print(f"[bold green]✓ Created branch:[/bold green] {name}")
            if from_branch:
                console.print(f"  [dim]From:[/dim] {from_branch}")

        elif action == "delete":
            if not name:
                console.print("[bold red]✗ Error: Branch name required[/bold red]")
                raise typer.Exit(1)

            task_obj = services["task_service"].get_task_by_name(task_name)
            if not task_obj:
                console.print(f"[bold red]✗ Error: Task '{task_name}' not found[/bold red]")
                raise typer.Exit(1)

            if services["branch_service"].delete_branch(task_obj.id, name):
                services["session"].commit()
                console.print(f"[bold green]✓ Deleted branch:[/bold green] {name}")
            else:
                console.print(f"[bold red]✗ Error: Branch '{name}' not found[/bold red]")
                raise typer.Exit(1)

        services["session"].close()

    except ValueError as e:
        console.print(f"[bold red]✗ Error: {e}[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        logger.exception("Unexpected error in branch")
        console.print(f"[bold red]✗ Unexpected error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def switch(
    task: Optional[str] = typer.Option(None, "--task", help="Task name"),
    branch: Optional[str] = typer.Option(None, "--branch", help="Branch name"),
) -> None:
    """Switch current task and/or branch."""
    try:
        services = get_services()

        # Validate task exists before setting current task
        if task:
            task_obj = services["task_service"].get_task_by_name(task)
            if not task_obj:
                console.print(f"[bold red]✗ Error: Task '{task}' not found[/bold red]")
                services["session"].close()
                raise typer.Exit(1)

            StateManager.set_current_task(task)
            console.print(f"[bold green]✓ Switched to task:[/bold green] {task}")

        # Validate branch if possible (requires a task to check against)
        if branch:
            task_name_for_branch = task or StateManager.get_current_task()
            if task_name_for_branch:
                task_obj_for_branch = services["task_service"].get_task_by_name(task_name_for_branch)
                if not task_obj_for_branch:
                    console.print(f"[bold red]✗ Error: Task '{task_name_for_branch}' not found[/bold red]")
                    services["session"].close()
                    raise typer.Exit(1)

                br = services["branch_service"].get_branch(task_obj_for_branch.id, branch)
                if not br:
                    console.print(f"[bold red]✗ Error: Branch '{branch}' not found for task '{task_name_for_branch}'[/bold red]")
                    services["session"].close()
                    raise typer.Exit(1)

            StateManager.set_current_branch(branch)
            console.print(f"[bold green]✓ Switched to branch:[/bold green] {branch}")

        if not task and not branch:
            console.print("[bold yellow]ⓘ Nothing to switch (use --task or --branch)[/bold yellow]")

        services["session"].close()

    except Exception as e:
        logger.exception("Unexpected error in switch")
        console.print(f"[bold red]✗ Unexpected error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def history(
    task: Optional[str] = typer.Option(None, "--task", help="Task name"),
    branch: Optional[str] = typer.Option(None, "--branch", help="Branch name"),
    limit: int = typer.Option(20, "--limit", help="Maximum commits to show"),
) -> None:
    """Show commit history for a branch."""
    try:
        task_name = task or StateManager.get_current_task()
        branch_name = branch or StateManager.get_current_branch() or "main"

        if not task_name:
            console.print("[bold red]✗ Error: Task not specified[/bold red]")
            raise typer.Exit(1)

        services = get_services()

        task_obj = services["task_service"].get_task_by_name(task_name)
        if not task_obj:
            console.print(f"[bold red]✗ Error: Task '{task_name}' not found[/bold red]")
            raise typer.Exit(1)

        commits = services["commit_service"].get_history(task_obj.id, branch_name, limit)
        services["session"].close()

        if commits:
            table = Table(title=f"History of {branch_name}")
            table.add_column("Commit ID", style="cyan")
            table.add_column("Message", style="white")
            table.add_column("Author", style="green")
            table.add_column("Created At", style="dim")
            table.add_column("Load/Unc", style="yellow")

            for c in commits:
                load_unc = "—"
                if c.cognitive_load is not None or c.uncertainty is not None:
                    load = c.cognitive_load or "—"
                    unc = c.uncertainty or "—"
                    load_unc = f"{load}/{unc}"

                table.add_row(
                    str(c.id)[:8],
                    c.message[:40],
                    c.author,
                    c.created_at.isoformat()[:19],
                    load_unc,
                )
            console.print(table)
        else:
            console.print(f"[dim]No commits in {branch_name}[/dim]")

    except ValueError as e:
        console.print(f"[bold red]✗ Error: {e}[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        logger.exception("Unexpected error in history")
        console.print(f"[bold red]✗ Unexpected error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def show(
    commit_id: str = typer.Argument(..., help="Commit ID (full or short)"),
) -> None:
    """Show full context of a commit."""
    try:
        from uuid import UUID

        services = get_services()

        # Try to parse as UUID
        try:
            cid = UUID(commit_id)
        except ValueError:
            console.print(f"[bold red]✗ Invalid commit ID: {commit_id}[/bold red]")
            raise typer.Exit(1)

        commit = services["commit_service"].get_commit(cid)
        if not commit:
            console.print(f"[bold red]✗ Commit not found: {commit_id}[/bold red]")
            raise typer.Exit(1)

        services["session"].close()

        console.print(f"[bold cyan]Commit:[/bold cyan] {commit.id}")
        console.print(f"[bold cyan]Message:[/bold cyan] {commit.message}")
        console.print(f"[bold cyan]Author:[/bold cyan] {commit.author}")
        console.print(f"[bold cyan]Created:[/bold cyan] {commit.created_at.isoformat()}")
        if commit.cognitive_load is not None:
            console.print(f"[bold cyan]Cognitive Load:[/bold cyan] {commit.cognitive_load}")
        if commit.uncertainty is not None:
            console.print(f"[bold cyan]Uncertainty:[/bold cyan] {commit.uncertainty}")

        console.print("\n[bold cyan]Context:[/bold cyan]")
        console.print(commit.full_context)

    except ValueError as e:
        console.print(f"[bold red]✗ Error: {e}[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        logger.exception("Unexpected error in show")
        console.print(f"[bold red]✗ Unexpected error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show current status."""
    try:
        state = StateManager.load()
        current_task = state.get("current_task")
        current_branch = state.get("current_branch")

        console.print("[bold]Status:[/bold]")
        if current_task:
            console.print(f"  [dim]Task:[/dim] {current_task}")
        else:
            console.print(f"  [dim]Task:[/dim] [yellow](not set)[/yellow]")

        if current_branch:
            console.print(f"  [dim]Branch:[/dim] {current_branch}")
        else:
            console.print(f"  [dim]Branch:[/dim] [yellow](not set)[/yellow]")

    except Exception as e:
        logger.exception("Unexpected error in status")
        console.print(f"[bold red]✗ Unexpected error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def context(
    task: Optional[str] = typer.Option(None, "--task", help="Task name (defaults to current task)"),
    branch: Optional[str] = typer.Option(None, "--branch", help="If provided, limit to this branch"),
    reverse: bool = typer.Option(False, "--reverse", help="Show newest first"),
) -> None:
    """Show full context for a task (concatenate commit contexts).

    If `--branch` is provided, shows contexts only from that branch's history.
    """
    try:
        services = get_services()

        # Resolve task: use provided --task or fall back to current state
        task_name = task or StateManager.get_current_task()
        if not task_name:
            console.print("[bold red]✗ Error: Task not specified and no current task set[/bold red]")
            raise typer.Exit(1)

        task_obj = services["task_service"].get_task_by_name(task_name)
        if not task_obj:
            console.print(f"[bold red]✗ Error: Task '{task_name}' not found[/bold red]")
            raise typer.Exit(1)

        commits: list[ContextCommit]
        if branch:
            commits = services["commit_service"].get_history(task_obj.id, branch, limit=1000)
        else:
            commits = services["commit_service"].get_commits_for_task(task_obj.id)

        services["session"].close()

        if not commits:
            console.print(f"[dim]No commits found for task {task_name}[/dim]")
            raise typer.Exit()

        if reverse:
            commits = list(reversed(commits))

        # Print concatenated contexts with headers per commit
        for c in commits:
            console.rule(f"Commit {str(c.id)[:8]} — {c.message}")
            console.print(f"Author: {c.author}  Created: {c.created_at.isoformat()}")
            if c.cognitive_load is not None or c.uncertainty is not None:
                load = c.cognitive_load if c.cognitive_load is not None else "—"
                unc = c.uncertainty if c.uncertainty is not None else "—"
                console.print(f"Metrics: {load}/{unc}")
            console.print()
            console.print(c.full_context)
            console.print()

    except Exception as e:
        logger.exception("Unexpected error in context")
        console.print(f"[bold red]✗ Unexpected error: {e}[/bold red]")
        raise typer.Exit(1)


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version",
        is_flag=True,
    ),
) -> None:
    """Mimir - Cognitive Context Management System."""
    if version:
        console.print("Mimir version 0.1.0")
        raise typer.Exit()


if __name__ == "__main__":
    app()
