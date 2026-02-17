"""Add external_id to tasks.

Revision ID: 002_add_external_id
Revises: 001_initial
Create Date: 2026-02-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002_add_external_id"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("external_id", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("tasks", "external_id")
