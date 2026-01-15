"""add_is_event_field_to_distinguish_live_sets_from_events

Revision ID: 75440e705062
Revises: e9ccb2dce2cd
Create Date: 2026-01-15 18:43:32.680409

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75440e705062'
down_revision: Union[str, None] = 'e9ccb2dce2cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_event field to distinguish live events from live sets
    op.add_column('dj_sets', sa.Column('is_event', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index(op.f('ix_dj_sets_is_event'), 'dj_sets', ['is_event'], unique=False)
    
    # Set is_event=True for existing live sets that have event information
    # (event_name, event_date, or venue_location) - these are likely events
    op.execute("""
        UPDATE dj_sets
        SET is_event = true
        WHERE source_type = 'LIVE'
        AND (event_name IS NOT NULL OR event_date IS NOT NULL OR venue_location IS NOT NULL)
    """)


def downgrade() -> None:
    # Remove is_event field
    op.drop_index(op.f('ix_dj_sets_is_event'), table_name='dj_sets')
    op.drop_column('dj_sets', 'is_event')
