"""Add projects and project_id to tasks.

Revision ID: 003_add_projects
Revises: 002_add_external_id
Create Date: 2026-02-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "003_add_projects"
down_revision = "002_add_external_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["projects.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_projects_name"), "projects", ["name"])

    # Create a default project for backward compatibility
    op.execute(
        "INSERT INTO projects (id, name, parent_id, created_at) "
        "VALUES (gen_random_uuid(), 'Default', NULL, NOW())"
    )

    # Add project_id to tasks (initially nullable)
    op.add_column("tasks", sa.Column("project_id", sa.UUID(), nullable=True))
    
    # Update existing tasks to use the default project
    op.execute(
        "UPDATE tasks SET project_id = (SELECT id FROM projects WHERE name = 'Default' LIMIT 1)"
    )
    
    # Make project_id NOT NULL
    op.alter_column("tasks", "project_id", existing_type=sa.UUID(), nullable=False)
    
    # Add foreign key constraint
    op.create_foreign_key("fk_tasks_project_id", "tasks", "projects", ["project_id"], ["id"])
    
    # Drop unique constraint on task name using dynamic SQL to handle auto-generated names
    # PostgreSQL may name it differently based on how it was created
    op.execute(
        """
        ALTER TABLE tasks DROP CONSTRAINT IF EXISTS uq_tasks_name;
        ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_name_key;
        """
    )
    
    # Add unique constraint for project_id + name
    op.create_unique_constraint("uq_project_task_name", "tasks", ["project_id", "name"])


def downgrade() -> None:
    # Drop unique constraint for project_id + name
    op.drop_constraint("uq_project_task_name", "tasks", type_="unique")
    
    # Re-add unique constraint on task name
    op.create_unique_constraint("uq_tasks_name", "tasks", ["name"])
    
    # Drop foreign key
    op.drop_constraint("fk_tasks_project_id", "tasks", type_="foreignkey")
    
    # Remove project_id from tasks
    op.drop_column("tasks", "project_id")
    
    # Drop projects table and its index
    op.drop_index(op.f("ix_projects_name"), table_name="projects")
    op.drop_table("projects")
