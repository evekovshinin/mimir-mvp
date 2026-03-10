from __future__ import annotations

from typing import Optional

from mimir.output import print_error, print_success, print_dim
from mimir.services.project_service import ProjectService


def handle_create_project(name: str, parent: Optional[str] = None) -> None:
    """Create a new project."""
    session = None
    from mimir.db import db_manager

    session = db_manager.get_session()
    try:
        project_service = ProjectService(session)

        # Validate parent exists if specified
        parent_id = None
        if parent:
            parent_obj = project_service.get_project_by_name(parent)
            if not parent_obj:
                print_error(f"Parent project '{parent}' not found")
                raise ValueError(f"Parent project '{parent}' not found")
            parent_id = parent_obj.id

        project = project_service.create_project(name=name, parent_id=parent_id)
        session.commit()

        print_success(f"Created project: {name}")
        if parent:
            print_dim(f"  Parent: {parent}")

    except ValueError:
        raise
    finally:
        if session:
            session.close()


def handle_list_projects() -> None:
    """List all projects in hierarchical view."""
    from mimir.db import db_manager

    session = db_manager.get_session()
    try:
        project_service = ProjectService(session)
        projects = project_service.list_projects()

        if not projects:
            print_dim("No projects found")
            return

        # Build hierarchy for display
        root_projects = project_service.list_root_projects()

        def print_project_tree(project, indent=0):
            """Recursively print project tree."""
            prefix = "  " * indent + ("├─ " if indent > 0 else "")
            print_dim(f"{prefix}{project.name}")
            children = project_service.list_child_projects(project.id)
            for child in children:
                print_project_tree(child, indent + 1)

        for project in root_projects:
            print_project_tree(project)

    finally:
        session.close()
