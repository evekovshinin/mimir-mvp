"""Command handlers for Mimir CLI."""
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from mimir.db import db_manager
from mimir.models import ContextCommit
from mimir.output import (
    print_error,
    print_success,
    print_task_created,
    print_commit_created,
    print_branch_created,
    print_branch_deleted,
    print_switched,
    print_branches_list,
    print_history_table,
    print_commit_details,
    print_context_concatenated,
    print_status,
    print_db_initialized,
    print_dim,
)
from mimir.services.branch_service import BranchService
from mimir.services.commit_service import CommitService
from mimir.services.task_service import TaskService
from mimir.state_manager import StateManager


def handle_init() -> None:
    """Initialize database."""
    print_success("Initializing database...")
    db_manager.init_db()
    print_db_initialized()


def handle_create_task(name: str, author: str = "default") -> None:
    """Create new task with main branch."""
    session = db_manager.get_session()
    try:
        service = TaskService(session)
        task = service.create_task(name=name, author=author)
        session.commit()
        
        StateManager.set_current_task(name)
        print_task_created(task)
    except ValueError as e:
        print_error(f"{e}")
        raise
    finally:
        session.close()


def handle_commit(
    task: Optional[str],
    branch: Optional[str],
    message: str,
    context_file: Optional[Path],
    context: Optional[str],
    author: str,
    cognitive_load: Optional[int],
    uncertainty: Optional[int],
) -> None:
    """Create commit on a branch."""
    session = db_manager.get_session()
    try:
        # Resolve task and branch
        task_name = task or StateManager.get_current_task()
        branch_name = branch or StateManager.get_current_branch() or "main"

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
            branch_name=branch_name,
            message=message,
            context=context_content,
            author=author,
            cognitive_load=cognitive_load,
            uncertainty=uncertainty,
        )
        session.commit()
        print_commit_created(new_commit, branch_name)

    except ValueError:
        raise
    finally:
        session.close()


def handle_branch_list(task: Optional[str]) -> None:
    """List branches for task."""
    session = db_manager.get_session()
    try:
        task_name = task or StateManager.get_current_task()
        
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

    except ValueError:
        raise
    finally:
        session.close()


def handle_branch_create(
    name: str,
    task: str,
    from_branch: Optional[str],
) -> None:
    """Create new branch."""
    session = db_manager.get_session()
    try:
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

    except ValueError:
        raise
    finally:
        session.close()


def handle_branch_delete(task: str, name: str) -> None:
    """Delete branch."""
    session = db_manager.get_session()
    try:
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

    except ValueError:
        raise
    finally:
        session.close()


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


def handle_history(
    task: Optional[str],
    branch: Optional[str],
    limit: int,
) -> None:
    """Show commit history."""
    session = db_manager.get_session()
    try:
        task_name = task or StateManager.get_current_task()
        branch_name = branch or StateManager.get_current_branch() or "main"

        if not task_name:
            print_error("Task not specified")
            raise ValueError("Task required")

        task_service = TaskService(session)
        task_obj = task_service.get_task_by_name(task_name)
        if not task_obj:
            print_error(f"Task '{task_name}' not found")
            raise ValueError("Task not found")

        commit_service = CommitService(session)
        commits = commit_service.get_history(task_obj.id, branch_name, limit)
        print_history_table(commits)

    except ValueError:
        raise
    finally:
        session.close()


def handle_show(commit_id: str) -> None:
    """Show full commit context."""
    session = db_manager.get_session()
    try:
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

    except ValueError:
        raise
    finally:
        session.close()


def handle_context(
    task: str,
    branch: Optional[str],
    reverse: bool,
) -> None:
    """Show full context for task."""
    session = db_manager.get_session()
    try:
        task_service = TaskService(session)
        task_obj = task_service.get_task_by_name(task)
        if not task_obj:
            print_error(f"Task '{task}' not found")
            raise ValueError("Task not found")

        commit_service = CommitService(session)
        
        commits: list[ContextCommit]
        if branch:
            commits = commit_service.get_history(task_obj.id, branch, limit=1000)
        else:
            commits = commit_service.get_commits_for_task(task_obj.id)

        if reverse:
            commits = list(reversed(commits))

        print_context_concatenated(commits)

    except ValueError:
        raise
    finally:
        session.close()


def handle_status() -> None:
    """Show current status."""
    current_task = StateManager.get_current_task()
    current_branch = StateManager.get_current_branch()
    print_status(current_task, current_branch)
