"""Add live recording fields

Revision ID: 9d0e1f2a3b4c
Revises: 8c9d0e1f2a3b
Create Date: 2026-01-15 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9d0e1f2a3b4c'
down_revision: Union[str, None] = '8c9d0e1f2a3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add live recording fields to dj_sets table
    op.add_column('dj_sets', sa.Column('is_live_recording', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('dj_sets', sa.Column('related_live_event_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_dj_sets_is_live_recording'), 'dj_sets', ['is_live_recording'], unique=False)
    op.create_index(op.f('ix_dj_sets_related_live_event_id'), 'dj_sets', ['related_live_event_id'], unique=False)
    op.create_foreign_key(
        'fk_dj_sets_related_live_event_id',
        'dj_sets', 'dj_sets',
        ['related_live_event_id'], ['id']
    )


def downgrade() -> None:
    # Remove live recording fields
    op.drop_constraint('fk_dj_sets_related_live_event_id', 'dj_sets', type_='foreignkey')
    op.drop_index(op.f('ix_dj_sets_related_live_event_id'), table_name='dj_sets')
    op.drop_index(op.f('ix_dj_sets_is_live_recording'), table_name='dj_sets')
    op.drop_column('dj_sets', 'related_live_event_id')
    op.drop_column('dj_sets', 'is_live_recording')
