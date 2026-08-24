"""make ticket decision nullable

Revision ID: e84c8c5aa1a8
Revises: 3102322c002c
Create Date: 2026-08-24 23:35:28.057093

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e84c8c5aa1a8'
down_revision: Union[str, Sequence[str], None] = '3102322c002c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # decision is now written after every node, not just the terminal one —
    # early nodes (classify, extract, route_decision) persist a row before
    # a decision exists.
    op.alter_column('tickets', 'decision', existing_type=sa.String(), nullable=True)
    # rows now start out unresolved (written as early as classify) instead of
    # only ever being inserted once already resolved.
    op.alter_column('tickets', 'resolved', existing_type=sa.Boolean(), server_default='false')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('tickets', 'resolved', existing_type=sa.Boolean(), server_default='true')
    op.alter_column('tickets', 'decision', existing_type=sa.String(), nullable=False)
