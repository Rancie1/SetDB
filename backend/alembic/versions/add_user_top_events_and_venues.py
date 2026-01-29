"""add_user_top_events_and_venues

Revision ID: add_top_events_venues
Revises: add_list_types_polymorphic
Create Date: 2026-01-29 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'add_top_events_venues'
down_revision: Union[str, Sequence[str], None] = 'add_list_types_polymorphic'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_top_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'event_id', name='uq_user_top_event'),
        sa.UniqueConstraint('user_id', 'order', name='uq_user_top_event_order'),
    )
    op.create_index('ix_user_top_events_user_id', 'user_top_events', ['user_id'])
    op.create_index('ix_user_top_events_event_id', 'user_top_events', ['event_id'])

    op.create_table(
        'user_top_venues',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('venue_name', sa.String(255), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'venue_name', name='uq_user_top_venue'),
        sa.UniqueConstraint('user_id', 'order', name='uq_user_top_venue_order'),
    )
    op.create_index('ix_user_top_venues_user_id', 'user_top_venues', ['user_id'])
    op.create_index('ix_user_top_venues_venue_name', 'user_top_venues', ['venue_name'])


def downgrade() -> None:
    op.drop_index('ix_user_top_venues_venue_name', table_name='user_top_venues')
    op.drop_index('ix_user_top_venues_user_id', table_name='user_top_venues')
    op.drop_table('user_top_venues')
    op.drop_index('ix_user_top_events_event_id', table_name='user_top_events')
    op.drop_index('ix_user_top_events_user_id', table_name='user_top_events')
    op.drop_table('user_top_events')
