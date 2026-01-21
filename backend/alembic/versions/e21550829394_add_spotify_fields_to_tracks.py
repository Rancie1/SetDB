"""add_spotify_fields_to_tracks

Revision ID: e21550829394
Revises: create_standalone_tracks
Create Date: 2026-01-21 15:29:04.162694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e21550829394'
down_revision: Union[str, None] = 'create_standalone_tracks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Spotify fields to tracks table
    op.add_column('tracks', sa.Column('spotify_url', sa.String(length=500), nullable=True))
    op.add_column('tracks', sa.Column('spotify_track_id', sa.String(length=255), nullable=True))
    
    # Add unique constraints for Spotify fields
    op.create_unique_constraint('uq_tracks_spotify_url', 'tracks', ['spotify_url'])
    op.create_unique_constraint('uq_tracks_spotify_track_id', 'tracks', ['spotify_track_id'])


def downgrade() -> None:
    # Remove unique constraints
    op.drop_constraint('uq_tracks_spotify_track_id', 'tracks', type_='unique')
    op.drop_constraint('uq_tracks_spotify_url', 'tracks', type_='unique')
    
    # Remove Spotify columns
    op.drop_column('tracks', 'spotify_track_id')
    op.drop_column('tracks', 'spotify_url')
