from __future__ import annotations

from typing import Optional

from mimir.output import (
    print_error,
    print_dim,
    print_branch_created,
    print_branch_deleted,
    print_branches_list,
)
from mimir.services.branch_service import BranchService
from mimir.services.task_service import TaskService
from ._common import with_session, resolve_task_name


def handle_branch(action: str, name: Optional[str], task: Optional[str], from_branch: Optional[str]) -> None:
    """Dispatch branch actions (list, create, delete)."""
    if action == "list":
        handle_branch_list(task)
    elif action == "create":
        if not name:
            print_error("Branch name required for create action")
            raise ValueError("Branch name required")
        task_name = resolve_task_name(task)
        if not task_name:
            print_error("Task not specified")
            raise ValueError("Task required")
        handle_branch_create(name, task_name, from_branch)
    elif action == "delete":
        if not name:
            print_error("Branch name required for delete action")
            raise ValueError("Branch name required")
        task_name = resolve_task_name(task)
        if not task_name:
            print_error("Task not specified")
            raise ValueError("Task required")
        handle_branch_delete(task_name, name)
    else:
        print_error(f"Unknown action: {action}. Use 'list', 'create', or 'delete'")
        raise ValueError(f"Unknown action: {action}")


@with_session
def handle_branch_list(task: Optional[str], session=None) -> None:
    """List branches for task."""
    task_name = resolve_task_name(task)

    if not task_name:
        print_dim("No task specified. Use --task to list branches.")
        return

    task_service = TaskService(session)
    task_obj = task_service.get_task_by_name(task_name)
    if not task_obj:
        print_error(f"Task '{task_name}' not found")
        raise ValueError(f"Task not found")

    branch_service = BranchService(session)
    branches = branch_service.list_branches(task_obj.id)
    print_branches_list(branches, task_name)


@with_session
def handle_branch_create(name: str, task: str, from_branch: Optional[str], session=None) -> None:
    """Create new branch."""
    task_service = TaskService(session)
    task_obj = task_service.get_task_by_name(task)
    if not task_obj:
        print_error(f"Task '{task}' not found")
        raise ValueError("Task not found")

    # Get from commit
    from_commit_id = None
    if from_branch:
        branch_service = BranchService(session)
        from_br = branch_service.get_branch(task_obj.id, from_branch)
        if not from_br:
            print_error(f"Branch '{from_branch}' not found")
            raise ValueError("Branch not found")
        from_commit_id = from_br.head_commit_id

    branch_service = BranchService(session)
    new_branch = branch_service.create_branch(
        task_id=task_obj.id,
        name=name,
        from_commit_id=from_commit_id,
    )
    session.commit()
    print_branch_created(name, from_branch)


@with_session
def handle_branch_delete(task: str, name: str, session=None) -> None:
    """Delete branch."""
    task_service = TaskService(session)
    task_obj = task_service.get_task_by_name(task)
    if not task_obj:
        print_error(f"Task '{task}' not found")
        raise ValueError("Task not found")

    branch_service = BranchService(session)
    if branch_service.delete_branch(task_obj.id, name):
        session.commit()
        print_branch_deleted(name)
    else:
        print_error(f"Branch '{name}' not found")
        raise ValueError("Branch not found")
