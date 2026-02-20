from __future__ import annotations

from typing import Optional

from mimir.output import print_context_concatenated, print_switched, print_dim
from mimir.services.commit_service import CommitService
from mimir.services.task_service import TaskService
from mimir.state_manager import StateManager

from ._common import with_session, resolve_task_name, require_task_name


@with_session
def handle_context(task: Optional[str], branch: Optional[str], reverse: bool, session=None) -> None:
    """Show full context for task."""
    task_name = resolve_task_name(task)
    require_task_name(task_name)

    task_service = TaskService(session)
    task_obj = task_service.get_task_by_name(task_name)
    if not task_obj:
        from mimir.output import print_error

        print_error(f"Task '{task_name}' not found")
        raise ValueError("Task not found")

    commit_service = CommitService(session)

    commits: list
    if branch:
        commits = commit_service.get_history(task_obj.id, branch, limit=1000)
    else:
        commits = commit_service.get_commits_for_task(task_obj.id)

    if reverse:
        commits = list(reversed(commits))

    print_context_concatenated(commits)


def handle_switch(task: Optional[str], branch: Optional[str]) -> None:
    """Switch current task and/or branch."""
    if task:
        StateManager.set_current_task(task)
    if branch:
        StateManager.set_current_branch(branch)

    if not task and not branch:
        print_dim("Nothing to switch (use --task or --branch)")
        return

    print_switched(task, branch)
