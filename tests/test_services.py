"""Unit tests for Mimir."""
import pytest
from pathlib import Path
from sqlalchemy.orm import Session

from mimir.db import DatabaseManager
from mimir.models import Base, Task, ContextCommit, Branch
from mimir.services.task_service import TaskService
from mimir.services.commit_service import CommitService
from mimir.services.branch_service import BranchService


@pytest.fixture
def db_session():
    """Create a test database session."""
    # Use SQLite for testing
    db_manager = DatabaseManager("sqlite:///:memory:")
    Base.metadata.create_all(db_manager.engine)
    
    session = db_manager.get_session()
    yield session
    session.close()


@pytest.fixture
def task_service(db_session):
    """Create task service."""
    return TaskService(db_session)


@pytest.fixture
def commit_service(db_session):
    """Create commit service."""
    return CommitService(db_session)


@pytest.fixture
def branch_service(db_session):
    """Create branch service."""
    return BranchService(db_session)


class TestTaskService:
    """Tests for TaskService."""

    def test_create_task(self, task_service, db_session):
        """Test creating a task."""
        task = task_service.create_task("TASK-42", author="test_user")
        db_session.commit()

        assert task.name == "TASK-42"
        assert task.id is not None

        # Verify main branch was created
        branches = db_session.query(Branch).filter(Branch.task_id == task.id).all()
        assert len(branches) == 1
        assert branches[0].name == "main"

    def test_create_duplicate_task(self, task_service, db_session):
        """Test creating duplicate task raises error."""
        task_service.create_task("TASK-42")
        
        with pytest.raises(ValueError, match="already exists"):
            task_service.create_task("TASK-42")

    def test_get_task_by_name(self, task_service, db_session):
        """Test getting task by name."""
        created_task = task_service.create_task("TEST-1")
        db_session.commit()

        retrieved = task_service.get_task_by_name("TEST-1")
        assert retrieved is not None
        assert retrieved.id == created_task.id

    def test_list_tasks(self, task_service, db_session):
        """Test listing tasks."""
        task_service.create_task("TASK-1")
        task_service.create_task("TASK-2")
        db_session.commit()

        tasks = task_service.list_tasks()
        assert len(tasks) == 2


class TestCommitService:
    """Tests for CommitService."""

    def test_create_commit(self, task_service, commit_service, db_session):
        """Test creating a commit."""
        task = task_service.create_task("TASK-42")
        db_session.commit()

        commit = commit_service.create_commit(
            task_id=task.id,
            branch_name="main",
            message="Initial context",
            context="This is the context",
            author="alice",
            cognitive_load=5,
            uncertainty=3,
        )
        db_session.commit()

        assert commit.message == "Initial context"
        assert commit.author == "alice"
        assert commit.cognitive_load == 5

        # Verify branch head was updated
        branch = db_session.query(Branch).filter(
            Branch.task_id == task.id,
            Branch.name == "main"
        ).first()
        assert branch.head_commit_id == commit.id

    def test_create_commit_with_parent(self, task_service, commit_service, db_session):
        """Test creating a commit with parent."""
        task = task_service.create_task("TASK-42")
        db_session.commit()

        # Create first commit
        commit1 = commit_service.create_commit(
            task_id=task.id,
            branch_name="main",
            message="First commit",
            context="Context 1",
            author="alice",
        )
        db_session.commit()

        # Create second commit (should have first as parent)
        commit2 = commit_service.create_commit(
            task_id=task.id,
            branch_name="main",
            message="Second commit",
            context="Context 2",
            author="alice",
        )
        db_session.commit()

        # Verify parent relationship
        parents = commit_service.get_commit_parents(commit2.id)
        assert len(parents) == 1
        assert parents[0].id == commit1.id

    def test_get_history(self, task_service, commit_service, db_session):
        """Test getting commit history."""
        task = task_service.create_task("TASK-42")
        db_session.commit()

        # Create multiple commits
        for i in range(3):
            commit_service.create_commit(
                task_id=task.id,
                branch_name="main",
                message=f"Commit {i}",
                context=f"Context {i}",
                author="alice",
            )
            db_session.commit()

        history = commit_service.get_history(task.id, "main")
        assert len(history) == 3

    def test_create_commit_invalid_branch(self, task_service, commit_service):
        """Test creating commit on non-existent branch."""
        task = task_service.create_task("TASK-42")

        with pytest.raises(ValueError, match="not found"):
            commit_service.create_commit(
                task_id=task.id,
                branch_name="non-existent",
                message="Test",
                context="Test",
                author="alice",
            )


class TestBranchService:
    """Tests for BranchService."""

    def test_create_branch(self, task_service, branch_service, db_session):
        """Test creating a branch."""
        task = task_service.create_task("TASK-42")
        db_session.commit()

        branch = branch_service.create_branch(task.id, "feature")
        db_session.commit()

        assert branch.name == "feature"
        assert branch.task_id == task.id

    def test_create_duplicate_branch(self, task_service, branch_service, db_session):
        """Test creating duplicate branch raises error."""
        task = task_service.create_task("TASK-42")
        db_session.commit()

        branch_service.create_branch(task.id, "feature")
        
        with pytest.raises(ValueError, match="already exists"):
            branch_service.create_branch(task.id, "feature")

    def test_list_branches(self, task_service, branch_service, db_session):
        """Test listing branches."""
        task = task_service.create_task("TASK-42")
        db_session.commit()

        branch_service.create_branch(task.id, "feature1")
        branch_service.create_branch(task.id, "feature2")
        db_session.commit()

        branches = branch_service.list_branches(task.id)
        names = {b.name for b in branches}
        
        assert "main" in names
        assert "feature1" in names
        assert "feature2" in names

    def test_delete_branch(self, task_service, branch_service, db_session):
        """Test deleting a branch."""
        task = task_service.create_task("TASK-42")
        db_session.commit()

        branch_service.create_branch(task.id, "feature")
        db_session.commit()

        result = branch_service.delete_branch(task.id, "feature")
        db_session.commit()

        assert result is True

        branch = branch_service.get_branch(task.id, "feature")
        assert branch is None

    def test_cannot_delete_main_branch(self, task_service, branch_service):
        """Test that main branch cannot be deleted."""
        task = task_service.create_task("TASK-42")

        with pytest.raises(ValueError, match="Cannot delete main branch"):
            branch_service.delete_branch(task.id, "main")

    def test_rename_branch(self, task_service, branch_service, db_session):
        """Test renaming a branch."""
        task = task_service.create_task("TASK-42")
        db_session.commit()

        branch_service.create_branch(task.id, "old-name")
        db_session.commit()

        branch = branch_service.rename_branch(task.id, "old-name", "new-name")
        db_session.commit()

        assert branch is not None
        assert branch.name == "new-name"

        old = branch_service.get_branch(task.id, "old-name")
        new = branch_service.get_branch(task.id, "new-name")

        assert old is None
        assert new is not None
