from __future__ import annotations

from pathlib import Path
from typing import Optional
from uuid import UUID

from mimir.output import (
    print_error,
    print_commit_created,
    print_history_table,
    print_commit_details,
)
from mimir.services.commit_service import CommitService
from mimir.services.task_service import TaskService
from ._common import with_session, resolve_task_name


@with_session
def handle_commit(
    task: Optional[str],
    branch: Optional[str],
    message: str,
    context_file: Optional[Path],
    context: Optional[str],
    author: str,
    cognitive_load: Optional[int],
    uncertainty: Optional[int],
    session=None,
) -> None:
    """Create commit on a branch."""
    # Resolve task and branch
    task_name = resolve_task_name(task)
    branch_name = branch or None

    if not task_name:
        print_error("Task not specified and no current task set")
        raise ValueError("Task required")

    # Get context
    if context_file:
        context_content = context_file.read_text()
    elif context:
        context_content = context
    else:
        print_error("No context provided (--context or --context-file)")
        raise ValueError("Context required")

    # Get task ID
    task_service = TaskService(session)
    task_obj = task_service.get_task_by_name(task_name)
    if not task_obj:
        print_error(f"Task '{task_name}' not found")
        raise ValueError(f"Task '{task_name}' not found")

    # Create commit
    commit_service = CommitService(session)
    new_commit = commit_service.create_commit(
        task_id=task_obj.id,
        branch_name=branch_name or "main",
        message=message,
        context=context_content,
        author=author,
        cognitive_load=cognitive_load,
        uncertainty=uncertainty,
    )
    session.commit()
    print_commit_created(new_commit, branch_name or "main")


@with_session
def handle_history(task: Optional[str], branch: Optional[str], limit: int, session=None) -> None:
    """Show commit history."""
    task_name = resolve_task_name(task)
    branch_name = branch or None

    if not task_name:
        print_error("Task not specified")
        raise ValueError("Task required")

    task_service = TaskService(session)
    task_obj = task_service.get_task_by_name(task_name)
    if not task_obj:
        print_error(f"Task '{task_name}' not found")
        raise ValueError("Task not found")

    commit_service = CommitService(session)
    commits = commit_service.get_history(task_obj.id, branch_name or "main", limit)
    print_history_table(commits)


@with_session
def handle_show(commit_id: str, session=None) -> None:
    """Show full commit context."""
    try:
        cid = UUID(commit_id)
    except ValueError:
        print_error(f"Invalid commit ID: {commit_id}")
        raise ValueError("Invalid UUID")

    commit_service = CommitService(session)
    commit = commit_service.get_commit(cid)
    if not commit:
        print_error(f"Commit not found: {commit_id}")
        raise ValueError("Commit not found")

    print_commit_details(commit)
