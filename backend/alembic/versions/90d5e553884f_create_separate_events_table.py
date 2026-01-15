"""create_separate_events_table

Revision ID: 90d5e553884f
Revises: 75440e705062
Create Date: 2026-01-15 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '90d5e553884f'
down_revision: Union[str, None] = '75440e705062'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create events table
    op.create_table('events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('dj_name', sa.String(length=255), nullable=False),
        sa.Column('event_name', sa.String(length=255), nullable=True),
        sa.Column('event_date', sa.Date(), nullable=True),
        sa.Column('venue_location', sa.String(length=255), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('confirmation_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_dj_name'), 'events', ['dj_name'], unique=False)
    op.create_index(op.f('ix_events_event_date'), 'events', ['event_date'], unique=False)
    op.create_index(op.f('ix_events_is_verified'), 'events', ['is_verified'], unique=False)
    op.create_index(op.f('ix_events_title'), 'events', ['title'], unique=False)
    
    # Migrate existing event data from dj_sets to events table
    op.execute("""
        INSERT INTO events (id, title, dj_name, event_name, event_date, venue_location, 
                           thumbnail_url, description, is_verified, confirmation_count, 
                           created_at, updated_at, created_by_id)
        SELECT id, title, dj_name, event_name, event_date, venue_location,
               thumbnail_url, description, is_verified, confirmation_count,
               created_at, updated_at, created_by_id
        FROM dj_sets
        WHERE is_event = true
    """)
    
    # Delete the event rows from dj_sets (they're now in the events table)
    op.execute("""
        DELETE FROM dj_sets
        WHERE is_event = true
    """)
    
    # Migrate event_confirmations to reference events table
    op.drop_constraint('uq_user_event_confirmation', 'event_confirmations', type_='unique')
    op.drop_constraint('event_confirmations_set_id_fkey', 'event_confirmations', type_='foreignkey')
    op.drop_index(op.f('ix_event_confirmations_set_id'), table_name='event_confirmations')
    # Rename column using ALTER TABLE
    op.execute("ALTER TABLE event_confirmations RENAME COLUMN set_id TO event_id")
    op.create_index(op.f('ix_event_confirmations_event_id'), 'event_confirmations', ['event_id'], unique=False)
    op.create_foreign_key('event_confirmations_event_id_fkey', 'event_confirmations', 'events', ['event_id'], ['id'])
    op.create_unique_constraint('uq_user_event_confirmation', 'event_confirmations', ['user_id', 'event_id'])
    
    # Migrate event_sets to reference events table
    op.drop_constraint('uq_event_set', 'event_sets', type_='unique')
    op.drop_constraint('event_sets_event_id_fkey', 'event_sets', type_='foreignkey')
    op.drop_index(op.f('ix_event_sets_event_id'), table_name='event_sets')
    
    # Update event_id foreign key to point to events table
    # First, ensure all event_ids in event_sets exist in events table
    op.execute("""
        DELETE FROM event_sets
        WHERE event_id NOT IN (SELECT id FROM events)
    """)
    
    op.create_foreign_key('event_sets_event_id_fkey', 'event_sets', 'events', ['event_id'], ['id'])
    op.create_index(op.f('ix_event_sets_event_id'), 'event_sets', ['event_id'], unique=False)
    op.create_unique_constraint('uq_event_set', 'event_sets', ['event_id', 'set_id'])
    
    # Remove event-related fields from dj_sets
    op.drop_index(op.f('ix_dj_sets_is_event'), table_name='dj_sets')
    op.drop_index(op.f('ix_dj_sets_is_verified'), table_name='dj_sets')
    op.drop_column('dj_sets', 'is_event')
    op.drop_column('dj_sets', 'is_verified')
    op.drop_column('dj_sets', 'confirmation_count')
    op.drop_column('dj_sets', 'event_name')
    op.drop_column('dj_sets', 'event_date')
    op.drop_column('dj_sets', 'venue_location')


def downgrade() -> None:
    # Add back event-related fields to dj_sets
    op.add_column('dj_sets', sa.Column('venue_location', sa.String(length=255), nullable=True))
    op.add_column('dj_sets', sa.Column('event_date', sa.Date(), nullable=True))
    op.add_column('dj_sets', sa.Column('event_name', sa.String(length=255), nullable=True))
    op.add_column('dj_sets', sa.Column('confirmation_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('dj_sets', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('dj_sets', sa.Column('is_event', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index(op.f('ix_dj_sets_is_verified'), 'dj_sets', ['is_verified'], unique=False)
    op.create_index(op.f('ix_dj_sets_is_event'), 'dj_sets', ['is_event'], unique=False)
    
    # Migrate data back from events to dj_sets
    op.execute("""
        UPDATE dj_sets
        SET event_name = e.event_name,
            event_date = e.event_date,
            venue_location = e.venue_location,
            is_verified = e.is_verified,
            confirmation_count = e.confirmation_count,
            is_event = true
        FROM events e
        WHERE dj_sets.id = e.id
    """)
    
    # Revert event_sets foreign key
    op.drop_constraint('uq_event_set', 'event_sets', type_='unique')
    op.drop_index(op.f('ix_event_sets_event_id'), table_name='event_sets')
    op.drop_constraint('event_sets_event_id_fkey', 'event_sets', type_='foreignkey')
    op.create_foreign_key('event_sets_event_id_fkey', 'event_sets', 'dj_sets', ['event_id'], ['id'])
    op.create_index(op.f('ix_event_sets_event_id'), 'event_sets', ['event_id'], unique=False)
    op.create_unique_constraint('uq_event_set', 'event_sets', ['event_id', 'set_id'])
    
    # Revert event_confirmations foreign key
    op.drop_constraint('uq_user_event_confirmation', 'event_confirmations', type_='unique')
    op.drop_constraint('event_confirmations_event_id_fkey', 'event_confirmations', type_='foreignkey')
    op.drop_index(op.f('ix_event_confirmations_event_id'), table_name='event_confirmations')
    # Rename column back using ALTER TABLE
    op.execute("ALTER TABLE event_confirmations RENAME COLUMN event_id TO set_id")
    op.create_index(op.f('ix_event_confirmations_set_id'), 'event_confirmations', ['set_id'], unique=False)
    op.create_foreign_key('event_confirmations_set_id_fkey', 'event_confirmations', 'dj_sets', ['set_id'], ['id'])
    op.create_unique_constraint('uq_user_event_confirmation', 'event_confirmations', ['user_id', 'set_id'])
    
    # Drop events table
    op.drop_index(op.f('ix_events_title'), table_name='events')
    op.drop_index(op.f('ix_events_is_verified'), table_name='events')
    op.drop_index(op.f('ix_events_event_date'), table_name='events')
    op.drop_index(op.f('ix_events_dj_name'), table_name='events')
    op.drop_table('events')
