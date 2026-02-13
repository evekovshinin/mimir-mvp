"""Initial schema creation.

Revision ID: 001_initial
Revises: 
Create Date: 2026-02-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema."""
    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create context_commits table
    op.create_table(
        "context_commits",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("message", sa.String(512), nullable=False),
        sa.Column("full_context", sa.Text(), nullable=False),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("cognitive_load", sa.SmallInteger(), nullable=True),
        sa.Column("uncertainty", sa.SmallInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create commit_parents table
    op.create_table(
        "commit_parents",
        sa.Column("child_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["context_commits.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["context_commits.id"]),
        sa.PrimaryKeyConstraint("child_id", "parent_id"),
        sa.UniqueConstraint("child_id", "parent_id", name="uq_commit_parent"),
    )

    # Create branches table
    op.create_table(
        "branches",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("head_commit_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["head_commit_id"], ["context_commits.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "name", name="uq_task_branch_name"),
    )

    # Create indexes
    op.create_index(op.f("ix_context_commits_task_id"), "context_commits", ["task_id"])
    op.create_index(op.f("ix_branches_task_id"), "branches", ["task_id"])
    op.create_index(op.f("ix_branches_head_commit_id"), "branches", ["head_commit_id"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(op.f("ix_branches_head_commit_id"), table_name="branches")
    op.drop_index(op.f("ix_branches_task_id"), table_name="branches")
    op.drop_index(op.f("ix_context_commits_task_id"), table_name="context_commits")
    op.drop_table("branches")
    op.drop_table("commit_parents")
    op.drop_table("context_commits")
    op.drop_table("tasks")
