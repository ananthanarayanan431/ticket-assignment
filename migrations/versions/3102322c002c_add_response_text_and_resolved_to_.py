"""add response_text and resolved to tickets

Revision ID: 3102322c002c
Revises: 76cfd790d8da
Create Date: 2026-08-24 13:27:30.393266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3102322c002c'
down_revision: Union[str, Sequence[str], None] = '76cfd790d8da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tickets', sa.Column('response_text', sa.Text(), nullable=True))
    op.add_column('tickets', sa.Column('resolved', sa.Boolean(), server_default='true', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tickets', 'resolved')
    op.drop_column('tickets', 'response_text')
