"""Remove set recordings, add recording_url and event_sets

Revision ID: e9ccb2dce2cd
Revises: 9d0e1f2a3b4c
Create Date: 2026-01-15 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e9ccb2dce2cd'
down_revision: Union[str, None] = '9d0e1f2a3b4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create event_sets table for many-to-many relationship between events and sets
    # This allows sets to be linked to events without being "recordings" of them
    op.create_table('event_sets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('set_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['event_id'], ['dj_sets.id'], ),
        sa.ForeignKeyConstraint(['set_id'], ['dj_sets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', 'set_id', name='uq_event_set')
    )
    op.create_index(op.f('ix_event_sets_event_id'), 'event_sets', ['event_id'], unique=False)
    op.create_index(op.f('ix_event_sets_set_id'), 'event_sets', ['set_id'], unique=False)
    
    # Migrate existing data: if a set was linked to a live event via related_live_event_id,
    # create an EventSet entry and preserve the relationship
    op.execute("""
        INSERT INTO event_sets (id, event_id, set_id, created_at)
        SELECT gen_random_uuid(), related_live_event_id, id, created_at
        FROM dj_sets
        WHERE related_live_event_id IS NOT NULL
        AND EXISTS (SELECT 1 FROM dj_sets d2 WHERE d2.id = dj_sets.related_live_event_id AND d2.source_type = 'LIVE')
    """)
    
    # Add recording_url column for live sets
    op.add_column('dj_sets', sa.Column('recording_url', sa.String(length=500), nullable=True))
    
    # Remove the old recording relationship columns
    op.drop_constraint('fk_dj_sets_related_live_event_id', 'dj_sets', type_='foreignkey')
    op.drop_index(op.f('ix_dj_sets_related_live_event_id'), table_name='dj_sets')
    op.drop_index(op.f('ix_dj_sets_is_live_recording'), table_name='dj_sets')
    op.drop_column('dj_sets', 'related_live_event_id')
    op.drop_column('dj_sets', 'is_live_recording')


def downgrade() -> None:
    # Add back the old columns
    op.add_column('dj_sets', sa.Column('is_live_recording', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('dj_sets', sa.Column('related_live_event_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_dj_sets_is_live_recording'), 'dj_sets', ['is_live_recording'], unique=False)
    op.create_index(op.f('ix_dj_sets_related_live_event_id'), 'dj_sets', ['related_live_event_id'], unique=False)
    op.create_foreign_key(
        'fk_dj_sets_related_live_event_id',
        'dj_sets', 'dj_sets',
        ['related_live_event_id'], ['id']
    )
    
    # Migrate data back from event_sets to related_live_event_id
    # Note: This will only restore one link per set (the first one found)
    op.execute("""
        UPDATE dj_sets
        SET related_live_event_id = (
            SELECT event_id FROM event_sets 
            WHERE event_sets.set_id = dj_sets.id 
            LIMIT 1
        ),
        is_live_recording = (
            SELECT CASE WHEN EXISTS (
                SELECT 1 FROM event_sets 
                WHERE event_sets.set_id = dj_sets.id
            ) THEN true ELSE false END
        )
        WHERE EXISTS (SELECT 1 FROM event_sets WHERE event_sets.set_id = dj_sets.id)
    """)
    
    # Remove recording_url column
    op.drop_column('dj_sets', 'recording_url')
    
    # Remove event_sets table
    op.drop_index(op.f('ix_event_sets_set_id'), table_name='event_sets')
    op.drop_index(op.f('ix_event_sets_event_id'), table_name='event_sets')
    op.drop_table('event_sets')
