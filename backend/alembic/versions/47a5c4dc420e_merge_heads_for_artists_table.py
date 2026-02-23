"""merge heads for artists table

Revision ID: 47a5c4dc420e
Revises: a1b2c3d4e5f6, b1bb84802035
Create Date: 2026-02-18 18:48:02.214584

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47a5c4dc420e'
down_revision: Union[str, None] = ('a1b2c3d4e5f6', 'b1bb84802035')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
