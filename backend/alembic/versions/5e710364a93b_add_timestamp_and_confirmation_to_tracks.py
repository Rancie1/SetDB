"""add_timestamp_and_confirmation_to_tracks

Revision ID: 5e710364a93b
Revises: 51039d2c6dd9
Create Date: 2026-01-19 15:42:09.840240

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5e710364a93b'
down_revision: Union[str, None] = '51039d2c6dd9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add timestamp_seconds column to set_tracks
    op.add_column('set_tracks', sa.Column('timestamp_seconds', sa.Integer(), nullable=True))
    
    # Create track_confirmations table
    op.create_table('track_confirmations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('track_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_confirmed', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['track_id'], ['set_tracks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'track_id', name='uq_user_track_confirmation')
    )
    op.create_index(op.f('ix_track_confirmations_track_id'), 'track_confirmations', ['track_id'], unique=False)
    op.create_index(op.f('ix_track_confirmations_user_id'), 'track_confirmations', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_track_confirmations_user_id'), table_name='track_confirmations')
    op.drop_index(op.f('ix_track_confirmations_track_id'), table_name='track_confirmations')
    op.drop_table('track_confirmations')
    op.drop_column('set_tracks', 'timestamp_seconds')
