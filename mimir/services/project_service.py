"""Project service for managing projects."""
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from mimir.models import Project

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project management."""

    def __init__(self, session: Session):
        """Initialize project service."""
        self.session = session

    def create_project(self, name: str, parent_id: UUID | None = None) -> Project:
        """Create a new project.
        
        Args:
            name: Project name (must be unique)
            parent_id: Optional parent project ID for hierarchy
            
        Returns:
            Created Project object
            
        Raises:
            ValueError: If project already exists or parent not found
        """
        # Check if project exists
        existing = self.session.query(Project).filter(Project.name == name).first()
        if existing:
            logger.error(f"Project '{name}' already exists")
            raise ValueError(f"Project '{name}' already exists")

        # Validate parent exists if specified
        if parent_id:
            parent = self.session.query(Project).filter(Project.id == parent_id).first()
            if not parent:
                logger.error(f"Parent project with id {parent_id} not found")
                raise ValueError(f"Parent project with id {parent_id} not found")

        # Create project
        project = Project(name=name, parent_id=parent_id)
        self.session.add(project)
        logger.info(f"Created project '{name}' with id {project.id}")
        return project

    def get_project(self, project_id: UUID) -> Project | None:
        """Get project by ID."""
        return self.session.query(Project).filter(Project.id == project_id).first()

    def get_project_by_name(self, name: str) -> Project | None:
        """Get project by name."""
        return self.session.query(Project).filter(Project.name == name).first()

    def list_projects(self, include_children: bool = True) -> list[Project]:
        """List all projects.
        
        Args:
            include_children: If True, includes child projects in relationships
            
        Returns:
            List of all projects
        """
        projects = self.session.query(Project).order_by(Project.name).all()
        return projects

    def list_root_projects(self) -> list[Project]:
        """List only root projects (those without parent)."""
        return (
            self.session.query(Project)
            .filter(Project.parent_id.is_(None))
            .order_by(Project.name)
            .all()
        )

    def list_child_projects(self, parent_id: UUID) -> list[Project]:
        """List child projects of a given parent."""
        return (
            self.session.query(Project)
            .filter(Project.parent_id == parent_id)
            .order_by(Project.name)
            .all()
        )

    def delete_project(self, project_id: UUID) -> bool:
        """Delete a project (and all its tasks by cascade).
        
        Args:
            project_id: Project ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        project = self.session.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.warning(f"Project with id {project_id} not found")
            return False

        self.session.delete(project)
        logger.info(f"Deleted project '{project.name}' with id {project_id}")
        return True

    def rename_project(self, project_id: UUID, new_name: str) -> Project | None:
        """Rename a project.
        
        Args:
            project_id: Project ID to rename
            new_name: New project name
            
        Returns:
            Updated Project or None if not found
            
        Raises:
            ValueError: If new name already exists
        """
        project = self.session.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.warning(f"Project with id {project_id} not found")
            return None

        # Check if new name already exists
        existing = self.session.query(Project).filter(Project.name == new_name).first()
        if existing and existing.id != project_id:
            logger.error(f"Project '{new_name}' already exists")
            raise ValueError(f"Project '{new_name}' already exists")

        old_name = project.name
        project.name = new_name
        logger.info(f"Renamed project from '{old_name}' to '{new_name}'")
        return project

    def get_project_hierarchy(self, project_id: UUID) -> dict:
        """Get full hierarchy of a project (with children).
        
        Returns:
            Dictionary representing the project tree
        """
        project = self.session.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {}

        children = self.list_child_projects(project_id)
        return {
            "id": str(project.id),
            "name": project.name,
            "parent_id": str(project.parent_id) if project.parent_id else None,
            "children": [self.get_project_hierarchy(child.id) for child in children],
        }
