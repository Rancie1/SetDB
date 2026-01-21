"""add_duration_days_to_events

Revision ID: 696c9a81d151
Revises: f86620c7f373
Create Date: 2026-01-19 16:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '696c9a81d151'
down_revision: Union[str, None] = 'f86620c7f373'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add duration_days column to events table (check if it already exists)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('events')]
    
    if 'duration_days' not in columns:
        op.add_column('events', sa.Column('duration_days', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove duration_days column from events table
    op.drop_column('events', 'duration_days')
