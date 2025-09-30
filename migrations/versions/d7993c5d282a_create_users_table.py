"""create users table

Revision ID: d7993c5d282a
Revises: 
Create Date: 2025-09-28 03:43:37.628347

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd7993c5d282a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Upgrade schema."""
    # enable pgcrypto extension for gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.Text(), nullable=False, unique=True),
        sa.Column('username', sa.Text(), nullable=False, unique=True),
        sa.Column('password_hash', sa.Text(), nullable=False),

        sa.Column('api_key_enc', sa.Text(), nullable=False),
        sa.Column('api_key_created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('api_key_expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('api_key_revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),

        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('meta', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb"))
    )

    # indexes
    op.create_index('users_username_idx', 'users', ['username'], unique=True)
    op.create_index('users_email_idx', 'users', [sa.text('lower(email)')], unique=True)
    op.create_index('users_api_key_enc_idx', 'users', ['api_key_enc'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('users_api_key_enc_idx', table_name='users')
    op.drop_index('users_email_idx', table_name='users')
    op.drop_index('users_username_idx', table_name='users')
    op.drop_table('users')
