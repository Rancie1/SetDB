"""create artists table

Revision ID: b1bb84802035
Revises: 9d0e1f2a3b4c
Create Date: 2026-02-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'b1bb84802035'
down_revision = '9d0e1f2a3b4c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'artists',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('spotify_artist_id', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('spotify_url', sa.String(500), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('genres', sa.String(500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('instagram_url', sa.String(500), nullable=True),
        sa.Column('soundcloud_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('artists')
