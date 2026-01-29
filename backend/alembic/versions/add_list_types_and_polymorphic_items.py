"""add_list_types_and_polymorphic_items

Revision ID: add_list_types_polymorphic
Revises: add_top_sets_fields
Create Date: 2026-01-29 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_list_types_polymorphic'
down_revision: Union[str, Sequence[str], None] = 'add_track_set_link_confirmations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if columns already exist (idempotent migration)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    lists_columns = [col['name'] for col in inspector.get_columns('lists')]
    list_items_columns = [col['name'] for col in inspector.get_columns('list_items')]
    list_items_indexes = [idx['name'] for idx in inspector.get_indexes('list_items')]
    list_items_constraints = [c['name'] for c in inspector.get_unique_constraints('list_items')]
    
    # Add list_type to lists table
    if 'list_type' not in lists_columns:
        op.add_column('lists', sa.Column('list_type', sa.String(50), nullable=False, server_default='sets'))
        op.create_index('ix_lists_list_type', 'lists', ['list_type'])
    
    # Add max_items to lists table
    if 'max_items' not in lists_columns:
        op.add_column('lists', sa.Column('max_items', sa.Integer(), nullable=True))
    
    # Make set_id nullable in list_items
    if 'set_id' in list_items_columns:
        # Check if it's already nullable
        set_id_col = [c for c in inspector.get_columns('list_items') if c['name'] == 'set_id'][0]
        if set_id_col['nullable'] is False:
            op.alter_column('list_items', 'set_id', nullable=True)
    
    # Add new foreign key columns for polymorphic items
    if 'event_id' not in list_items_columns:
        op.add_column('list_items', sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key('fk_list_items_event_id', 'list_items', 'events', ['event_id'], ['id'])
        op.create_index('ix_list_items_event_id', 'list_items', ['event_id'])
    
    if 'track_id' not in list_items_columns:
        op.add_column('list_items', sa.Column('track_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key('fk_list_items_track_id', 'list_items', 'tracks', ['track_id'], ['id'])
        op.create_index('ix_list_items_track_id', 'list_items', ['track_id'])
    
    if 'venue_name' not in list_items_columns:
        op.add_column('list_items', sa.Column('venue_name', sa.String(255), nullable=True))
        op.create_index('ix_list_items_venue_name', 'list_items', ['venue_name'])
    
    # Drop old unique constraint if it exists
    if 'uq_list_set_item' in list_items_constraints:
        op.drop_constraint('uq_list_set_item', 'list_items', type_='unique')
    
    # Create new unique constraints for each item type
    # PostgreSQL unique constraints allow NULLs, so these will work correctly
    if 'uq_list_set_item' not in list_items_constraints:
        op.create_unique_constraint('uq_list_set_item', 'list_items', ['list_id', 'set_id'])
    
    if 'uq_list_event_item' not in list_items_constraints:
        op.create_unique_constraint('uq_list_event_item', 'list_items', ['list_id', 'event_id'])
    
    if 'uq_list_track_item' not in list_items_constraints:
        op.create_unique_constraint('uq_list_track_item', 'list_items', ['list_id', 'track_id'])
    
    if 'uq_list_venue_item' not in list_items_constraints:
        op.create_unique_constraint('uq_list_venue_item', 'list_items', ['list_id', 'venue_name'])
    
    # Add check constraint to ensure exactly one item type is set
    op.create_check_constraint(
        'check_exactly_one_item_type',
        'list_items',
        '(set_id IS NOT NULL)::int + (event_id IS NOT NULL)::int + (track_id IS NOT NULL)::int + (venue_name IS NOT NULL)::int = 1'
    )


def downgrade() -> None:
    # Drop check constraint
    op.drop_constraint('check_exactly_one_item_type', 'list_items', type_='check')
    
    # Drop unique constraints
    op.drop_constraint('uq_list_venue_item', 'list_items', type_='unique')
    op.drop_constraint('uq_list_track_item', 'list_items', type_='unique')
    op.drop_constraint('uq_list_event_item', 'list_items', type_='unique')
    op.drop_constraint('uq_list_set_item', 'list_items', type_='unique')
    
    # Recreate old unique constraint
    op.create_unique_constraint('uq_list_set_item', 'list_items', ['list_id', 'set_id'])
    
    # Drop new columns
    op.drop_index('ix_list_items_venue_name', table_name='list_items')
    op.drop_column('list_items', 'venue_name')
    
    op.drop_index('ix_list_items_track_id', table_name='list_items')
    op.drop_constraint('fk_list_items_track_id', 'list_items', type_='foreignkey')
    op.drop_column('list_items', 'track_id')
    
    op.drop_index('ix_list_items_event_id', table_name='list_items')
    op.drop_constraint('fk_list_items_event_id', 'list_items', type_='foreignkey')
    op.drop_column('list_items', 'event_id')
    
    # Make set_id non-nullable again
    op.alter_column('list_items', 'set_id', nullable=False)
    
    # Drop columns from lists
    op.drop_column('lists', 'max_items')
    op.drop_index('ix_lists_list_type', table_name='lists')
    op.drop_column('lists', 'list_type')
