"""create_standalone_tracks_system

Revision ID: create_standalone_tracks
Revises: add_track_ratings_reviews
Create Date: 2026-01-21 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'create_standalone_tracks'
down_revision: Union[str, None] = '5e710364a93b'  # add_timestamp_and_confirmation_to_tracks
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tracks table (independent track entity)
    op.create_table('tracks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('track_name', sa.String(length=255), nullable=False),
        sa.Column('artist_name', sa.String(length=255), nullable=True),
        sa.Column('soundcloud_url', sa.String(length=500), nullable=True),
        sa.Column('soundcloud_track_id', sa.String(length=255), nullable=True),
        sa.Column('spotify_url', sa.String(length=500), nullable=True),
        sa.Column('spotify_track_id', sa.String(length=255), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('soundcloud_url', name='uq_tracks_soundcloud_url'),
        sa.UniqueConstraint('soundcloud_track_id', name='uq_tracks_soundcloud_track_id'),
        sa.UniqueConstraint('spotify_url', name='uq_tracks_spotify_url'),
        sa.UniqueConstraint('spotify_track_id', name='uq_tracks_spotify_track_id')
    )
    op.create_index(op.f('ix_tracks_track_name'), 'tracks', ['track_name'], unique=False)
    op.create_index(op.f('ix_tracks_artist_name'), 'tracks', ['artist_name'], unique=False)
    op.create_index(op.f('ix_tracks_created_by_id'), 'tracks', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_tracks_created_at'), 'tracks', ['created_at'], unique=False)
    
    # Create track_set_links table (many-to-many between tracks and sets)
    op.create_table('track_set_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('track_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('set_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('added_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('timestamp_minutes', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['added_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['set_id'], ['dj_sets.id'], ),
        sa.ForeignKeyConstraint(['track_id'], ['tracks.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('track_id', 'set_id', name='uq_track_set_link')
    )
    op.create_index(op.f('ix_track_set_links_track_id'), 'track_set_links', ['track_id'], unique=False)
    op.create_index(op.f('ix_track_set_links_set_id'), 'track_set_links', ['set_id'], unique=False)
    op.create_index(op.f('ix_track_set_links_added_by_id'), 'track_set_links', ['added_by_id'], unique=False)
    
    # Create user_top_tracks table
    op.create_table('user_top_tracks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('track_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['track_id'], ['tracks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'track_id', name='uq_user_top_track'),
        sa.UniqueConstraint('user_id', 'order', name='uq_user_top_track_order')
    )
    op.create_index(op.f('ix_user_top_tracks_user_id'), 'user_top_tracks', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_top_tracks_track_id'), 'user_top_tracks', ['track_id'], unique=False)
    
    # Update track_ratings to reference tracks instead of set_tracks
    op.drop_constraint('track_ratings_track_id_fkey', 'track_ratings', type_='foreignkey')
    op.create_foreign_key('track_ratings_track_id_fkey', 'track_ratings', 'tracks', ['track_id'], ['id'])
    
    # Update track_reviews to reference tracks instead of set_tracks
    op.drop_constraint('track_reviews_track_id_fkey', 'track_reviews', type_='foreignkey')
    op.create_foreign_key('track_reviews_track_id_fkey', 'track_reviews', 'tracks', ['track_id'], ['id'])


def downgrade() -> None:
    # Revert foreign keys
    op.drop_constraint('track_reviews_track_id_fkey', 'track_reviews', type_='foreignkey')
    op.create_foreign_key('track_reviews_track_id_fkey', 'track_reviews', 'set_tracks', ['track_id'], ['id'])
    
    op.drop_constraint('track_ratings_track_id_fkey', 'track_ratings', type_='foreignkey')
    op.create_foreign_key('track_ratings_track_id_fkey', 'track_ratings', 'set_tracks', ['track_id'], ['id'])
    
    # Drop user_top_tracks table
    op.drop_index(op.f('ix_user_top_tracks_track_id'), table_name='user_top_tracks')
    op.drop_index(op.f('ix_user_top_tracks_user_id'), table_name='user_top_tracks')
    op.drop_table('user_top_tracks')
    
    # Drop track_set_links table
    op.drop_index(op.f('ix_track_set_links_added_by_id'), table_name='track_set_links')
    op.drop_index(op.f('ix_track_set_links_set_id'), table_name='track_set_links')
    op.drop_index(op.f('ix_track_set_links_track_id'), table_name='track_set_links')
    op.drop_table('track_set_links')
    
    # Drop tracks table
    op.drop_index(op.f('ix_tracks_created_at'), table_name='tracks')
    op.drop_index(op.f('ix_tracks_created_by_id'), table_name='tracks')
    op.drop_index(op.f('ix_tracks_artist_name'), table_name='tracks')
    op.drop_index(op.f('ix_tracks_track_name'), table_name='tracks')
    op.drop_constraint('uq_tracks_spotify_track_id', 'tracks', type_='unique')
    op.drop_constraint('uq_tracks_spotify_url', 'tracks', type_='unique')
    op.drop_constraint('uq_tracks_soundcloud_track_id', 'tracks', type_='unique')
    op.drop_constraint('uq_tracks_soundcloud_url', 'tracks', type_='unique')
    op.drop_table('tracks')
