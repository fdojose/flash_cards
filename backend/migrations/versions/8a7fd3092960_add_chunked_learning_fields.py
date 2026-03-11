"""add chunked learning fields

Revision ID: 8a7fd3092960
Revises: 116b3b0c0f1b
Create Date: 2025-08-03 23:26:07.129678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a7fd3092960'
down_revision: Union[str, None] = '116b3b0c0f1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add chunked learning fields to user_learning_sets
    op.add_column('user_learning_sets', sa.Column('chunk_number', sa.Integer(), default=1, nullable=True))
    op.add_column('user_learning_sets', sa.Column('total_chunks', sa.Integer(), nullable=True))
    op.add_column('user_learning_sets', sa.Column('chunk_size', sa.Integer(), nullable=True))
    op.add_column('user_learning_sets', sa.Column('total_dataset_size', sa.Integer(), nullable=True))
    
    # Set defaults for existing records
    op.execute("UPDATE user_learning_sets SET chunk_number = 1 WHERE chunk_number IS NULL")
    op.execute("UPDATE user_learning_sets SET chunk_size = 100 WHERE chunk_size IS NULL")


def downgrade() -> None:
    # Remove chunked learning fields
    op.drop_column('user_learning_sets', 'total_dataset_size')
    op.drop_column('user_learning_sets', 'chunk_size')
    op.drop_column('user_learning_sets', 'total_chunks')
    op.drop_column('user_learning_sets', 'chunk_number')
