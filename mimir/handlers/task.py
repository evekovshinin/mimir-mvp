from __future__ import annotations

from pathlib import Path
from typing import Optional

from mimir.output import (
    print_error,
    print_task_created,
    print_dim,
    print_tasks_list,
)
from mimir.services.project_service import ProjectService
from mimir.services.task_service import TaskService
from mimir.services.commit_service import CommitService
from mimir.state_manager import StateManager

from ._common import with_session


@with_session
def handle_create_task(
    project: Optional[str] = None,
    name: str = None,
    author: str = "default",
    external_id: str | None = None,
    message: Optional[str] = None,
    context_file: Optional[Path] = None,
    context: Optional[str] = None,
    session=None,
) -> None:
    """Create new task in a project with main branch, optionally create initial commit."""
    try:
        # Resolve project
        project_name = project
        if not project_name:
            print_error("Project not specified. Use --project flag.")
            raise ValueError("Project is required")

        project_service = ProjectService(session)
        project_obj = project_service.get_project_by_name(project_name)
        if not project_obj:
            print_error(f"Project '{project_name}' not found")
            raise ValueError(f"Project '{project_name}' not found")

        task_service = TaskService(session)
        task = task_service.create_task(
            project_id=project_obj.id,
            name=name,
            author=author,
            external_id=external_id,
        )
        session.commit()

        StateManager.set_current_task(name)
        print_task_created(task)

        # If initial commit data provided, create first commit on main
        if message or context_file or context:
            # Resolve context content
            if context_file:
                context_content = context_file.read_text()
            elif context:
                context_content = context
            else:
                print_error("No context provided for initial commit")
                raise ValueError("Context required for initial commit")

            commit_service = CommitService(session)
            new_commit = commit_service.create_commit(
                task_id=task.id,
                branch_name="main",
                message=message or "Initial commit",
                context=context_content,
                author=author,
            )
            session.commit()
            # reuse same print function available in output
            from mimir.output import print_commit_created

            print_commit_created(new_commit, "main")

    except ValueError:
        raise


@with_session
def handle_list_tasks(project: Optional[str] = None, session=None) -> None:
    """List tasks, optionally filtered by project."""
    project_service = ProjectService(session)
    task_service = TaskService(session)
    commit_service = CommitService(session)

    # If project specified, get its ID
    project_id = None
    project_name_display = None
    if project:
        project_obj = project_service.get_project_by_name(project)
        if not project_obj:
            print_error(f"Project '{project}' not found")
            raise ValueError(f"Project '{project}' not found")
        project_id = project_obj.id
        project_name_display = project_obj.name

    tasks = task_service.list_tasks(project_id=project_id)
    tasks_info: list[dict] = []
    for t in tasks:
        commits = commit_service.get_commits_for_task(t.id)
        last_commit_at = commits[-1].created_at if commits else None
        tasks_info.append(
            {
                "name": t.name,
                "project": t.project.name,
                "external_id": getattr(t, "external_id", None),
                "created_at": t.created_at,
                "commits_count": len(commits),
                "last_commit_at": last_commit_at,
            }
        )

    print_tasks_list(tasks_info, project_name=project_name_display)
