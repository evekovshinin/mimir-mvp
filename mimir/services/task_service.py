"""Task service for managing tasks."""
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from mimir.models import Branch, Project, Task

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task management."""

    def __init__(self, session: Session):
        """Initialize task service."""
        self.session = session

    def create_task(self, project_id: UUID, name: str, author: str = "default", external_id: str | None = None) -> Task:
        """Create a new task with main branch.
        
        Args:
            project_id: Project ID that this task belongs to
            name: Task name (unique within the project)
            author: Task author
            external_id: Optional external identifier
            
        Returns:
            Created Task object
            
        Raises:
            ValueError: If task already exists or project not found
        """
        # Validate project exists
        project = self.session.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project with id {project_id} not found")
            raise ValueError(f"Project with id {project_id} not found")

        # Check if task already exists in this project
        existing = (
            self.session.query(Task)
            .filter(Task.project_id == project_id, Task.name == name)
            .first()
        )
        if existing:
            logger.error(f"Task '{name}' already exists in project '{project.name}'")
            raise ValueError(f"Task '{name}' already exists in this project")

        # Create task
        task = Task(project_id=project_id, name=name, external_id=external_id)
        self.session.add(task)
        self.session.flush()  # Get the task ID

        # Create main branch
        main_branch = Branch(task_id=task.id, name="main", head_commit_id=None)
        self.session.add(main_branch)

        logger.info(f"Created task '{name}' in project '{project.name}' with id {task.id}")
        return task

    def get_task(self, task_id: UUID) -> Task | None:
        """Get task by ID."""
        return self.session.query(Task).filter(Task.id == task_id).first()

    def get_task_by_name(self, name: str) -> Task | None:
        """Get task by name (searches all projects)."""
        return self.session.query(Task).filter(Task.name == name).first()

    def get_task_by_name_in_project(self, project_id: UUID, name: str) -> Task | None:
        """Get task by name within a specific project."""
        return (
            self.session.query(Task)
            .filter(Task.project_id == project_id, Task.name == name)
            .first()
        )

    def list_tasks(self, project_id: UUID | None = None) -> list[Task]:
        """List tasks, optionally filtered by project.
        
        Args:
            project_id: If provided, list only tasks in this project
            
        Returns:
            List of tasks
        """
        query = self.session.query(Task)
        if project_id:
            query = query.filter(Task.project_id == project_id)
        return query.all()

    def delete_task(self, task_id: UUID) -> bool:
        """Delete a task."""
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False

        self.session.delete(task)
        logger.info(f"Deleted task {task_id}")
        return True
