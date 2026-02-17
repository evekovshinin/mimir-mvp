"""CLI interface for Mimir - streamlined dispatcher delegating to handlers and output."""
from pathlib import Path
from typing import Optional
from uuid import UUID

import typer

from mimir.config import logger, settings
from mimir.db import db_manager
from mimir.handlers import (
    handle_branch,
    handle_commit,
    handle_context,
    handle_create_task,
    handle_list_tasks,
    handle_history,
    handle_init,
    handle_show,
    handle_status,
    handle_switch,
)
from mimir.output import print_error, print_version
from mimir.services.branch_service import BranchService
from mimir.services.commit_service import CommitService
from mimir.services.task_service import TaskService
from mimir.state_manager import StateManager

app = typer.Typer(help="Mimir - Cognitive Context Management System")


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
        handle_init(url)
    except Exception as e:
        logger.exception("Unexpected error in init")
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def create_task(
    name: str = typer.Argument(..., help="Task name (e.g., TASK-42)"),
    author: str = typer.Option("default", "--author", help="Task creator"),
    external_id: Optional[str] = typer.Option(None, "--external-id", help="External task id (e.g. JIRA)"),
    message: Optional[str] = typer.Option(None, "--message", help="Initial commit message"),
    context_file: Optional[Path] = typer.Option(None, "--context-file", help="File with context content"),
    context: Optional[str] = typer.Option(None, "--context", help="Inline context"),
) -> None:
    """Create a new task with main branch."""
    try:
        handle_create_task(name, author, external_id, message, context_file, context)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        logger.exception("Unexpected error in create_task")
        print_error(str(e))
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
        handle_commit(task, branch, message, context_file, context, author, cognitive_load, uncertainty)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        logger.exception("Unexpected error in commit")
        print_error(str(e))
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
        handle_branch(action, name, task, from_branch)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        logger.exception("Unexpected error in branch")
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def switch(
    task: Optional[str] = typer.Option(None, "--task", help="Task name"),
    branch: Optional[str] = typer.Option(None, "--branch", help="Branch name"),
) -> None:
    """Switch current task and/or branch."""
    try:
        handle_switch(task, branch)
    except Exception as e:
        logger.exception("Unexpected error in switch")
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def history(
    task: Optional[str] = typer.Option(None, "--task", help="Task name"),
    branch: Optional[str] = typer.Option(None, "--branch", help="Branch name"),
    limit: int = typer.Option(20, "--limit", help="Maximum commits to show"),
) -> None:
    """Show commit history for a branch."""
    try:
        handle_history(task, branch, limit)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        logger.exception("Unexpected error in history")
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def show(
    commit_id: str = typer.Argument(..., help="Commit ID (full or short)"),
) -> None:
    """Show full context of a commit."""
    try:
        handle_show(commit_id)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        logger.exception("Unexpected error in show")
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show current status."""
    try:
        handle_status()
    except Exception as e:
        logger.exception("Unexpected error in status")
        print_error(str(e))
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
        handle_context(task, branch, reverse)
    except Exception as e:
        logger.exception("Unexpected error in context")
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def tasks() -> None:
    """List all tasks with stats."""
    try:
        handle_list_tasks()
    except Exception as e:
        logger.exception("Unexpected error in tasks")
        print_error(str(e))
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
        print_version()
        raise typer.Exit()


if __name__ == "__main__":
    app()
