"""Branch service for managing branches."""
import logging
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from mimir.models import Branch, Task

logger = logging.getLogger(__name__)


class BranchService:
    """Service for branch management."""

    def __init__(self, session: Session):
        """Initialize branch service."""
        self.session = session

    def create_branch(self, task_id: UUID, name: str, from_commit_id: UUID | None = None) -> Branch:
        """Create a new branch.
        
        Args:
            task_id: Task ID
            name: Branch name
            from_commit_id: Create branch from this commit (optional)
            
        Returns:
            Created Branch object
            
        Raises:
            ValueError: If task not found or branch already exists
        """
        # Check if task exists
        task = self.session.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            raise ValueError(f"Task {task_id} not found")

        # Check if branch already exists
        existing = self.session.query(Branch).filter(
            and_(Branch.task_id == task_id, Branch.name == name)
        ).first()
        if existing:
            logger.error(f"Branch '{name}' already exists for task {task_id}")
            raise ValueError(f"Branch '{name}' already exists")

        # Create branch
        branch = Branch(task_id=task_id, name=name, head_commit_id=from_commit_id)
        self.session.add(branch)

        logger.info(f"Created branch '{name}' for task {task_id}")
        return branch

    def get_branch(self, task_id: UUID, name: str) -> Branch | None:
        """Get branch by name."""
        return self.session.query(Branch).filter(
            and_(Branch.task_id == task_id, Branch.name == name)
        ).first()

    def list_branches(self, task_id: UUID) -> list[Branch]:
        """List all branches for a task."""
        return self.session.query(Branch).filter(Branch.task_id == task_id).all()

    def delete_branch(self, task_id: UUID, name: str) -> bool:
        """Delete a branch.
        
        Args:
            task_id: Task ID
            name: Branch name
            
        Returns:
            True if deleted, False if not found
        """
        branch = self.get_branch(task_id, name)
        if not branch:
            logger.error(f"Branch '{name}' not found for task {task_id}")
            return False

        if name == "main":
            logger.error("Cannot delete main branch")
            raise ValueError("Cannot delete main branch")

        self.session.delete(branch)
        logger.info(f"Deleted branch '{name}' from task {task_id}")
        return True

    def rename_branch(self, task_id: UUID, old_name: str, new_name: str) -> Branch | None:
        """Rename a branch.
        
        Args:
            task_id: Task ID
            old_name: Old branch name
            new_name: New branch name
            
        Returns:
            Renamed Branch object or None if not found
        """
        branch = self.get_branch(task_id, old_name)
        if not branch:
            logger.error(f"Branch '{old_name}' not found")
            return None

        # Check if new name already exists
        existing = self.get_branch(task_id, new_name)
        if existing:
            logger.error(f"Branch '{new_name}' already exists")
            raise ValueError(f"Branch '{new_name}' already exists")

        branch.name = new_name
        logger.info(f"Renamed branch '{old_name}' to '{new_name}'")
        return branch
