"""Commit service for managing context commits."""
import logging
from uuid import UUID

from sqlalchemy import and_, select, text
from sqlalchemy.orm import Session

from mimir.models import Branch, ContextCommit, CommitParent, Task

logger = logging.getLogger(__name__)


class CommitService:
    """Service for commit management."""

    def __init__(self, session: Session):
        """Initialize commit service."""
        self.session = session

    def create_commit(
        self,
        task_id: UUID,
        branch_name: str,
        message: str,
        context: str,
        author: str = "default",
        cognitive_load: int | None = None,
        uncertainty: int | None = None,
    ) -> ContextCommit:
        """Create a new commit on a branch.
        
        Args:
            task_id: Task ID
            branch_name: Branch name
            message: Commit message
            context: Full context (snapshot)
            author: Commit author
            cognitive_load: Optional cognitive load metric (0-10)
            uncertainty: Optional uncertainty metric (0-10)
            
        Returns:
            Created ContextCommit object
            
        Raises:
            ValueError: If branch or task not found
        """
        # Get task
        task = self.session.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            raise ValueError(f"Task {task_id} not found")

        # Get branch
        branch = self.session.query(Branch).filter(
            and_(Branch.task_id == task_id, Branch.name == branch_name)
        ).first()
        if not branch:
            logger.error(f"Branch '{branch_name}' not found for task {task_id}")
            raise ValueError(f"Branch '{branch_name}' not found")

        # Create commit
        commit = ContextCommit(
            task_id=task_id,
            message=message,
            full_context=context,
            author=author,
            cognitive_load=cognitive_load,
            uncertainty=uncertainty,
        )
        self.session.add(commit)
        self.session.flush()

        # Link to parent commit if exists
        if branch.head_commit_id:
            parent_relationship = CommitParent(
                child_id=commit.id,
                parent_id=branch.head_commit_id,
            )
            self.session.add(parent_relationship)
            logger.info(f"Created commit {commit.id} with parent {branch.head_commit_id}")

        # Update branch head
        branch.head_commit_id = commit.id

        logger.info(
            f"Created commit {commit.id} on branch '{branch_name}' for task {task_id}"
        )
        return commit

    def get_commit(self, commit_id: UUID) -> ContextCommit | None:
        """Get commit by ID."""
        return self.session.query(ContextCommit).filter(ContextCommit.id == commit_id).first()

    def get_commit_parents(self, commit_id: UUID) -> list[ContextCommit]:
        """Get parent commits of a commit."""
        commit = self.get_commit(commit_id)
        if not commit:
            return []

        return self.session.query(ContextCommit).join(
            CommitParent,
            ContextCommit.id == CommitParent.parent_id,
        ).filter(CommitParent.child_id == commit_id).all()

    def get_history(self, task_id: UUID, branch_name: str, limit: int = 100) -> list[ContextCommit]:
        """Get commit history for a branch using recursive CTE.
        
        Args:
            task_id: Task ID
            branch_name: Branch name
            limit: Maximum number of commits to return
            
        Returns:
            List of commits in reverse chronological order
        """
        # Get branch
        branch = self.session.query(Branch).filter(
            and_(Branch.task_id == task_id, Branch.name == branch_name)
        ).first()
        
        if not branch or not branch.head_commit_id:
            logger.warning(f"Branch '{branch_name}' not found or has no commits")
            return []

        # Use recursive CTE to traverse commit history
        query = text("""
            WITH RECURSIVE commit_history AS (
                -- Base case: start from branch head
                SELECT 
                    cc.id,
                    cc.task_id,
                    cc.message,
                    cc.full_context,
                    cc.author,
                    cc.cognitive_load,
                    cc.uncertainty,
                    cc.created_at,
                    1 as depth
                FROM context_commits cc
                WHERE cc.id = :head_commit_id
                
                UNION ALL
                
                -- Recursive case: find parents
                SELECT 
                    cc.id,
                    cc.task_id,
                    cc.message,
                    cc.full_context,
                    cc.author,
                    cc.cognitive_load,
                    cc.uncertainty,
                    cc.created_at,
                    ch.depth + 1
                FROM context_commits cc
                JOIN commit_parents cp ON cc.id = cp.parent_id
                JOIN commit_history ch ON cp.child_id = ch.id
                WHERE ch.depth < :limit
            )
            SELECT * FROM commit_history
            ORDER BY depth, created_at DESC
        """)

        result = self.session.execute(
            query,
            {"head_commit_id": str(branch.head_commit_id), "limit": limit},
        )

        commits = []
        for row in result:
            commit = ContextCommit(
                id=UUID(row[0]),
                task_id=UUID(row[1]),
                message=row[2],
                full_context=row[3],
                author=row[4],
                cognitive_load=row[5],
                uncertainty=row[6],
                created_at=row[7],
            )
            commits.append(commit)

        logger.info(f"Retrieved {len(commits)} commits from history")
        return commits

    def merge_commit(
        self,
        task_id: UUID,
        target_branch: str,
        source_commit_id: UUID,
        message: str,
        author: str = "default",
    ) -> ContextCommit:
        """Create a merge commit (commit with multiple parents).
        
        Args:
            task_id: Task ID
            target_branch: Target branch name
            source_commit_id: Commit ID to merge
            message: Merge commit message
            author: Commit author
            
        Returns:
            Created merge commit
            
        Raises:
            ValueError: If branch or commit not found
        """
        # Get target branch
        branch = self.session.query(Branch).filter(
            and_(Branch.task_id == task_id, Branch.name == target_branch)
        ).first()
        if not branch:
            logger.error(f"Target branch '{target_branch}' not found")
            raise ValueError(f"Target branch '{target_branch}' not found")

        if not branch.head_commit_id:
            logger.error(f"Target branch '{target_branch}' has no commits")
            raise ValueError(f"Target branch '{target_branch}' has no commits")

        # Get source commit
        source_commit = self.get_commit(source_commit_id)
        if not source_commit:
            logger.error(f"Source commit {source_commit_id} not found")
            raise ValueError(f"Source commit {source_commit_id} not found")

        # Create merge commit (empty context - could be filled with merged context)
        merge_commit = ContextCommit(
            task_id=task_id,
            message=message,
            full_context="",  # In real scenario, would contain merged context
            author=author,
        )
        self.session.add(merge_commit)
        self.session.flush()

        # Add both parents
        parent1 = CommitParent(child_id=merge_commit.id, parent_id=branch.head_commit_id)
        parent2 = CommitParent(child_id=merge_commit.id, parent_id=source_commit_id)
        self.session.add(parent1)
        self.session.add(parent2)

        # Update branch head
        branch.head_commit_id = merge_commit.id

        logger.info(
            f"Created merge commit {merge_commit.id} "
            f"with parents {branch.head_commit_id} and {source_commit_id}"
        )
        return merge_commit
