"""change_timestamp_from_seconds_to_minutes

Revision ID: f86620c7f373
Revises: 5e710364a93b
Create Date: 2026-01-19 15:53:16.981824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f86620c7f373'
down_revision: Union[str, None] = '5e710364a93b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert timestamp_seconds to timestamp_minutes
    # First, convert existing seconds to minutes (divide by 60) and change type
    op.execute("""
        ALTER TABLE set_tracks 
        ADD COLUMN timestamp_minutes NUMERIC(10, 2);
    """)
    
    op.execute("""
        UPDATE set_tracks
        SET timestamp_minutes = ROUND(timestamp_seconds / 60.0, 2)
        WHERE timestamp_seconds IS NOT NULL
    """)
    
    # Drop old column
    op.drop_column('set_tracks', 'timestamp_seconds')


def downgrade() -> None:
    # Convert timestamp_minutes back to timestamp_seconds
    # Add column back
    op.add_column('set_tracks', sa.Column('timestamp_seconds', sa.Integer(), nullable=True))
    
    # Convert minutes back to seconds (multiply by 60)
    op.execute("""
        UPDATE set_tracks
        SET timestamp_seconds = ROUND(timestamp_minutes * 60, 0)::INTEGER
        WHERE timestamp_minutes IS NOT NULL
    """)
    
    # Drop new column
    op.drop_column('set_tracks', 'timestamp_minutes')
