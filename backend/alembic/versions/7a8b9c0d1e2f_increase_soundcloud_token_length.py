"""Increase SoundCloud token length

Revision ID: 7a8b9c0d1e2f
Revises: 584424dda9ee
Create Date: 2026-01-14 20:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, None] = '584424dda9ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change VARCHAR(500) to TEXT for SoundCloud tokens
    op.alter_column('users', 'soundcloud_access_token',
                    existing_type=sa.VARCHAR(length=500),
                    type_=sa.Text(),
                    existing_nullable=True)
    op.alter_column('users', 'soundcloud_refresh_token',
                    existing_type=sa.VARCHAR(length=500),
                    type_=sa.Text(),
                    existing_nullable=True)


def downgrade() -> None:
    # Revert TEXT back to VARCHAR(500)
    op.alter_column('users', 'soundcloud_access_token',
                    existing_type=sa.Text(),
                    type_=sa.VARCHAR(length=500),
                    existing_nullable=True)
    op.alter_column('users', 'soundcloud_refresh_token',
                    existing_type=sa.Text(),
                    type_=sa.VARCHAR(length=500),
                    existing_nullable=True)
