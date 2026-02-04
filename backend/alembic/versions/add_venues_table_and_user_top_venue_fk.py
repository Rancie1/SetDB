"""add_venues_table_and_user_top_venue_fk

Revision ID: add_venues_fk
Revises: add_top_events_venues
Create Date: 2026-01-29 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'add_venues_fk'
down_revision: Union[str, Sequence[str], None] = 'add_top_events_venues'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create venues table
    op.create_table(
        'venues',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('location', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_venues_name', 'venues', ['name'])

    # Add venue_id to user_top_venues (nullable first for backfill)
    op.add_column('user_top_venues', sa.Column('venue_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Backfill: create Venue row for each distinct venue_name, then set venue_id
    op.execute(sa.text("""
        INSERT INTO venues (id, name, created_at)
        SELECT gen_random_uuid(), vn, now()
        FROM (SELECT DISTINCT venue_name AS vn FROM user_top_venues WHERE venue_name IS NOT NULL) t
    """))
    op.execute(sa.text("""
        UPDATE user_top_venues utv
        SET venue_id = (SELECT id FROM venues v WHERE v.name = utv.venue_name LIMIT 1)
        WHERE utv.venue_name IS NOT NULL
    """))
    # Remove rows that could not be backfilled (null venue_name or no matching venue)
    op.execute(sa.text("DELETE FROM user_top_venues WHERE venue_id IS NULL"))

    # Drop old constraint and index on venue_name, then drop column
    op.drop_constraint('uq_user_top_venue', 'user_top_venues', type_='unique')
    op.drop_index('ix_user_top_venues_venue_name', table_name='user_top_venues')
    op.drop_column('user_top_venues', 'venue_name')

    # Make venue_id non-nullable and add FK + unique
    op.alter_column('user_top_venues', 'venue_id', nullable=False)
    op.create_foreign_key(
        'fk_user_top_venues_venue_id', 'user_top_venues', 'venues',
        ['venue_id'], ['id']
    )
    op.create_unique_constraint('uq_user_top_venue', 'user_top_venues', ['user_id', 'venue_id'])
    op.create_index('ix_user_top_venues_venue_id', 'user_top_venues', ['venue_id'])


def downgrade() -> None:
    op.drop_index('ix_user_top_venues_venue_id', table_name='user_top_venues')
    op.drop_constraint('uq_user_top_venue', 'user_top_venues', type_='unique')
    op.drop_constraint('fk_user_top_venues_venue_id', 'user_top_venues', type_='foreignkey')
    op.add_column('user_top_venues', sa.Column('venue_name', sa.String(255), nullable=True))
    op.execute(sa.text("""
        UPDATE user_top_venues utv
        SET venue_name = (SELECT name FROM venues v WHERE v.id = utv.venue_id)
    """))
    op.alter_column('user_top_venues', 'venue_name', nullable=False)
    op.drop_column('user_top_venues', 'venue_id')
    op.create_unique_constraint('uq_user_top_venue', 'user_top_venues', ['user_id', 'venue_name'])
    op.create_index('ix_user_top_venues_venue_name', 'user_top_venues', ['venue_name'])
    op.drop_index('ix_venues_name', table_name='venues')
    op.drop_table('venues')
