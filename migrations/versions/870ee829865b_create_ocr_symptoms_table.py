"""create ocr_symptoms table

Revision ID: 870ee829865b
Revises: f2483b6f04f2
Create Date: 2025-10-05 16:46:06.232653

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '870ee829865b'
down_revision: Union[str, Sequence[str], None] = 'f2483b6f04f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure pgcrypto is available
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # Create symptoms table
    op.create_table(
        "ocr_symptoms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("input", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("analysis", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("status", postgresql.ENUM("not_completed", "completed", name="status_enum", create_type=False), nullable=False, server_default=sa.text("'not_completed'::status_enum")),
        sa.Column("meta", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    op.create_index("ocr_symptoms_user_id_idx", "ocr_symptoms", ["user_id"])
    op.create_index("ocr_symptoms_id_idx", "ocr_symptoms", ["id"], unique=True)

def downgrade() -> None:

    # drop symptoms table and indexes
    op.drop_index("ocr_symptoms_user_id_idx", table_name="ocr_symptoms")
    op.drop_index("ocr_symptoms_id_idx", table_name="ocr_symptoms")
    op.drop_table("ocr_symptoms")
