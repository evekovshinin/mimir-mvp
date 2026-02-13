"""ORM models for Mimir."""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Task(Base):
    """Task model."""

    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    commits: Mapped[list["ContextCommit"]] = relationship(
        "ContextCommit", back_populates="task", cascade="all, delete-orphan"
    )
    branches: Mapped[list["Branch"]] = relationship(
        "Branch", back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name={self.name})>"


class ContextCommit(Base):
    """Context commit model (immutable snapshot)."""

    __tablename__ = "context_commits"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    message: Mapped[str] = mapped_column(String(512), nullable=False)
    full_context: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    cognitive_load: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    uncertainty: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    task: Mapped[Task] = relationship("Task", back_populates="commits")
    parents: Mapped[list["ContextCommit"]] = relationship(
        "ContextCommit",
        secondary="commit_parents",
        primaryjoin="ContextCommit.id == CommitParent.child_id",
        secondaryjoin="ContextCommit.id == CommitParent.parent_id",
        foreign_keys="[CommitParent.child_id, CommitParent.parent_id]",
        viewonly=True,
    )
    branches: Mapped[list["Branch"]] = relationship(
        "Branch", back_populates="head_commit", foreign_keys="Branch.head_commit_id"
    )

    def __repr__(self) -> str:
        return f"<ContextCommit(id={self.id}, task_id={self.task_id}, message={self.message[:50]})>"


class CommitParent(Base):
    """Commit parent relationship (supports merge)."""

    __tablename__ = "commit_parents"
    __table_args__ = (
        UniqueConstraint("child_id", "parent_id", name="uq_commit_parent"),
    )

    child_id: Mapped[UUID] = mapped_column(ForeignKey("context_commits.id"), primary_key=True)
    parent_id: Mapped[UUID] = mapped_column(ForeignKey("context_commits.id"), primary_key=True)

    def __repr__(self) -> str:
        return f"<CommitParent(child_id={self.child_id}, parent_id={self.parent_id})>"


class Branch(Base):
    """Branch model (pointer to commit)."""

    __tablename__ = "branches"
    __table_args__ = (UniqueConstraint("task_id", "name", name="uq_task_branch_name"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    head_commit_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("context_commits.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    task: Mapped[Task] = relationship("Task", back_populates="branches")
    head_commit: Mapped[Optional[ContextCommit]] = relationship(
        "ContextCommit", back_populates="branches", foreign_keys=[head_commit_id]
    )

    def __repr__(self) -> str:
        return f"<Branch(id={self.id}, task_id={self.task_id}, name={self.name})>"


def init_db(database_url: str) -> None:
    """Initialize database schema."""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
