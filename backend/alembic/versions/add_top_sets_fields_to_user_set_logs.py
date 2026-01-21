"""add_top_sets_fields_to_user_set_logs

Revision ID: add_top_sets_fields
Revises: 9d0e1f2a3b4c
Create Date: 2026-01-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_top_sets_fields'
down_revision: Union[str, Sequence[str], None] = ('696c9a81d151', '9d0e1f2a3b4c')  # Merge both heads
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if columns already exist (in case migration was partially run)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('user_set_logs')]
    indexes = [idx['name'] for idx in inspector.get_indexes('user_set_logs')]
    
    # Add is_top_set column if it doesn't exist
    if 'is_top_set' not in columns:
        op.add_column('user_set_logs', sa.Column('is_top_set', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add top_set_order column if it doesn't exist
    if 'top_set_order' not in columns:
        op.add_column('user_set_logs', sa.Column('top_set_order', sa.Integer(), nullable=True))
    
    # Create index on is_top_set for faster queries if it doesn't exist
    if 'ix_user_set_logs_is_top_set' not in indexes:
        op.create_index('ix_user_set_logs_is_top_set', 'user_set_logs', ['is_top_set'])


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_user_set_logs_is_top_set', table_name='user_set_logs')
    
    # Drop columns
    op.drop_column('user_set_logs', 'top_set_order')
    op.drop_column('user_set_logs', 'is_top_set')
