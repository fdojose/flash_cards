"""add timer support to learning sets

Revision ID: af151a1a4ca9
Revises: 6accffb54c14
Create Date: 2025-08-04 00:26:10.366735

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af151a1a4ca9'
down_revision: Union[str, None] = '6accffb54c14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add timer support fields to user_learning_sets
    op.add_column('user_learning_sets', sa.Column('timer_enabled', sa.Boolean(), default=False, nullable=False))
    op.add_column('user_learning_sets', sa.Column('timer_seconds', sa.Integer(), default=30, nullable=True))
    op.add_column('user_learning_sets', sa.Column('timer_mode', sa.String(20), default='optional', nullable=True))  # 'optional', 'strict', 'disabled'
    
    # Set default values for existing records
    op.execute("UPDATE user_learning_sets SET timer_enabled = false WHERE timer_enabled IS NULL")
    op.execute("UPDATE user_learning_sets SET timer_seconds = 30 WHERE timer_seconds IS NULL")
    op.execute("UPDATE user_learning_sets SET timer_mode = 'optional' WHERE timer_mode IS NULL")


def downgrade() -> None:
    # Remove timer support fields
    op.drop_column('user_learning_sets', 'timer_mode')
    op.drop_column('user_learning_sets', 'timer_seconds')
    op.drop_column('user_learning_sets', 'timer_enabled')
