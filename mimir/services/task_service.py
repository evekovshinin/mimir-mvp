"""Task service for managing tasks."""
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from mimir.models import Branch, Task

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task management."""

    def __init__(self, session: Session):
        """Initialize task service."""
        self.session = session

    def create_task(self, name: str, author: str = "default") -> Task:
        """Create a new task with main branch.
        
        Args:
            name: Task name (should be unique)
            author: Task author
            
        Returns:
            Created Task object
            
        Raises:
            ValueError: If task already exists
        """
        # Check if task exists
        existing = self.session.query(Task).filter(Task.name == name).first()
        if existing:
            logger.error(f"Task '{name}' already exists")
            raise ValueError(f"Task '{name}' already exists")

        # Create task
        task = Task(name=name)
        self.session.add(task)
        self.session.flush()  # Get the task ID

        # Create main branch
        main_branch = Branch(task_id=task.id, name="main", head_commit_id=None)
        self.session.add(main_branch)

        logger.info(f"Created task '{name}' with id {task.id}")
        return task

    def get_task(self, task_id: UUID) -> Task | None:
        """Get task by ID."""
        return self.session.query(Task).filter(Task.id == task_id).first()

    def get_task_by_name(self, name: str) -> Task | None:
        """Get task by name."""
        return self.session.query(Task).filter(Task.name == name).first()

    def list_tasks(self) -> list[Task]:
        """List all tasks."""
        return self.session.query(Task).all()

    def delete_task(self, task_id: UUID) -> bool:
        """Delete a task."""
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False

        self.session.delete(task)
        logger.info(f"Deleted task {task_id}")
        return True
