"""create symptoms table

Revision ID: f2483b6f04f2
Revises: d7993c5d282a
Create Date: 2025-09-30 14:35:51.535106
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f2483b6f04f2"
down_revision: Union[str, Sequence[str], None] = "d7993c5d282a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # Ensure pgcrypto is available
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # Define ENUM types
    sex_enum = postgresql.ENUM("male", "female", "other", name="sex_enum", create_type=False)
    status_enum = postgresql.ENUM("in_review", "completed", name="status_enum", create_type=False)

    # Create enum types explicitly
    sex_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)

    # Create symptoms table
    op.create_table(
        "symptoms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("sex", sex_enum, nullable=False),
        sa.Column("symptoms", sa.Text(), nullable=False),
        sa.Column("duration", sa.Text(), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("additional_notes", sa.Text(), nullable=True),
        sa.Column("analysis", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("status", status_enum, nullable=False, server_default=sa.text("'in_review'::status_enum")),
        sa.Column("meta", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    op.create_index("ix_symptoms_user_id", "symptoms", ["user_id"])


def downgrade() -> None:
    bind = op.get_bind()

    # drop symptoms table and indexes
    op.drop_index("ix_symptoms_user_id", table_name="symptoms")
    op.drop_table("symptoms")

    # drop enum types 
    postgresql.ENUM(name="sex_enum").drop(bind, checkfirst=True)
    postgresql.ENUM(name="status_enum").drop(bind, checkfirst=True)