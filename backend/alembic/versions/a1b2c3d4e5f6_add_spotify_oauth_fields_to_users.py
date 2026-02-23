"""Add Spotify OAuth fields to users

Revision ID: a1b2c3d4e5f6
Revises: f3f1de32e562
Create Date: 2026-02-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f3f1de32e562'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('spotify_user_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('spotify_access_token', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('spotify_refresh_token', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('spotify_token_expires_at', sa.DateTime(), nullable=True))
    op.create_unique_constraint('uq_users_spotify_user_id', 'users', ['spotify_user_id'])
    op.create_index('ix_users_spotify_user_id', 'users', ['spotify_user_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_spotify_user_id', table_name='users')
    op.drop_constraint('uq_users_spotify_user_id', 'users', type_='unique')
    op.drop_column('users', 'spotify_token_expires_at')
    op.drop_column('users', 'spotify_refresh_token')
    op.drop_column('users', 'spotify_access_token')
    op.drop_column('users', 'spotify_user_id')
