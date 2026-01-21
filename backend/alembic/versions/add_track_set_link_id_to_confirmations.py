"""add_track_set_link_id_to_confirmations

Revision ID: add_track_set_link_confirmations
Revises: e21550829394
Create Date: 2026-01-21 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_track_set_link_confirmations'
down_revision: Union[str, Sequence[str], None] = ('e21550829394', 'add_top_sets_fields')  # Merge both heads
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make track_id nullable
    op.alter_column('track_confirmations', 'track_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=True)
    
    # Add track_set_link_id column
    op.add_column('track_confirmations', sa.Column('track_set_link_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_track_confirmations_track_set_link_id'), 'track_confirmations', ['track_set_link_id'], unique=False)
    op.create_foreign_key('track_confirmations_track_set_link_id_fkey', 'track_confirmations', 'track_set_links', ['track_set_link_id'], ['id'])
    
    # Drop old unique constraint
    op.drop_constraint('uq_user_track_confirmation', 'track_confirmations', type_='unique')
    
    # Add new unique constraints (one for each type)
    op.create_unique_constraint('uq_user_set_track_confirmation', 'track_confirmations', ['user_id', 'track_id'])
    op.create_unique_constraint('uq_user_track_set_link_confirmation', 'track_confirmations', ['user_id', 'track_set_link_id'])


def downgrade() -> None:
    # Remove new unique constraints
    op.drop_constraint('uq_user_track_set_link_confirmation', 'track_confirmations', type_='unique')
    op.drop_constraint('uq_user_set_track_confirmation', 'track_confirmations', type_='unique')
    
    # Restore old unique constraint
    op.create_unique_constraint('uq_user_track_confirmation', 'track_confirmations', ['user_id', 'track_id'])
    
    # Remove track_set_link_id column
    op.drop_constraint('track_confirmations_track_set_link_id_fkey', 'track_confirmations', type_='foreignkey')
    op.drop_index(op.f('ix_track_confirmations_track_set_link_id'), table_name='track_confirmations')
    op.drop_column('track_confirmations', 'track_set_link_id')
    
    # Make track_id not nullable again
    op.alter_column('track_confirmations', 'track_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=False)
