"""Add event verification fields

Revision ID: 8c9d0e1f2a3b
Revises: 7a8b9c0d1e2f
Create Date: 2026-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8c9d0e1f2a3b'
down_revision: Union[str, None] = '7a8b9c0d1e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add verification fields to dj_sets table
    op.add_column('dj_sets', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('dj_sets', sa.Column('confirmation_count', sa.Integer(), nullable=False, server_default='0'))
    op.create_index(op.f('ix_dj_sets_is_verified'), 'dj_sets', ['is_verified'], unique=False)
    
    # Create event_confirmations table
    op.create_table('event_confirmations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('set_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['set_id'], ['dj_sets.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'set_id', name='uq_user_event_confirmation')
    )
    op.create_index(op.f('ix_event_confirmations_user_id'), 'event_confirmations', ['user_id'], unique=False)
    op.create_index(op.f('ix_event_confirmations_set_id'), 'event_confirmations', ['set_id'], unique=False)


def downgrade() -> None:
    # Drop event_confirmations table
    op.drop_index(op.f('ix_event_confirmations_set_id'), table_name='event_confirmations')
    op.drop_index(op.f('ix_event_confirmations_user_id'), table_name='event_confirmations')
    op.drop_table('event_confirmations')
    
    # Remove verification fields from dj_sets table
    op.drop_index(op.f('ix_dj_sets_is_verified'), table_name='dj_sets')
    op.drop_column('dj_sets', 'confirmation_count')
    op.drop_column('dj_sets', 'is_verified')
