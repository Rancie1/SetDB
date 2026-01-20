"""add_set_track_model_for_track_tagging

Revision ID: 51039d2c6dd9
Revises: 90d5e553884f
Create Date: 2026-01-19 15:36:06.297110

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '51039d2c6dd9'
down_revision: Union[str, None] = '90d5e553884f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create set_tracks table
    op.create_table('set_tracks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('set_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('added_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('track_name', sa.String(length=255), nullable=False),
        sa.Column('artist_name', sa.String(length=255), nullable=True),
        sa.Column('soundcloud_url', sa.String(length=500), nullable=True),
        sa.Column('soundcloud_track_id', sa.String(length=255), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['added_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['set_id'], ['dj_sets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('set_id', 'track_name', 'artist_name', name='uq_set_track')
    )
    op.create_index(op.f('ix_set_tracks_added_by_id'), 'set_tracks', ['added_by_id'], unique=False)
    op.create_index(op.f('ix_set_tracks_set_id'), 'set_tracks', ['set_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_set_tracks_set_id'), table_name='set_tracks')
    op.drop_index(op.f('ix_set_tracks_added_by_id'), table_name='set_tracks')
    op.drop_table('set_tracks')
