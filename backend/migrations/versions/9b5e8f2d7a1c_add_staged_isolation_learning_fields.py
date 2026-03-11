"""add staged isolation learning fields

Revision ID: 9b5e8f2d7a1c
Revises: 8a7fd3092960
Create Date: 2025-08-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b5e8f2d7a1c'
down_revision: Union[str, None] = '8a7fd3092960'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add batch tracking columns to user_learning_sets
    op.add_column('user_learning_sets', sa.Column('current_batch_start', sa.Integer(), default=1))
    op.add_column('user_learning_sets', sa.Column('current_batch_end', sa.Integer()))  
    op.add_column('user_learning_sets', sa.Column('isolation_phase', sa.Boolean(), default=True))
    op.add_column('user_learning_sets', sa.Column('mastered_up_to', sa.Integer(), default=0))
    op.add_column('user_learning_sets', sa.Column('batch_size', sa.Integer(), default=5))
    
    # Add accuracy tracking columns to user_element_reviews
    op.add_column('user_element_reviews', sa.Column('accuracy_percentage', sa.Float(), default=0.0))
    op.add_column('user_element_reviews', sa.Column('attempts_in_window', sa.Integer(), default=0))
    
    # Update existing learning sets with reasonable defaults
    op.execute("""
        UPDATE user_learning_sets 
        SET current_batch_end = LEAST(5, COALESCE(total_dataset_size, 5))
        WHERE current_batch_end IS NULL
    """)
    
    # Update existing reviews with calculated accuracy from existing attempts
    op.execute("""
        UPDATE user_element_reviews 
        SET accuracy_percentage = (
            SELECT COALESCE(
                AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END), 
                0.0
            )
            FROM user_field_attempts 
            WHERE user_field_attempts.user_id = user_element_reviews.user_id 
            AND user_field_attempts.element_id = user_element_reviews.element_id
        )
    """)


def downgrade() -> None:
    # Remove accuracy tracking columns from user_element_reviews
    op.drop_column('user_element_reviews', 'attempts_in_window')
    op.drop_column('user_element_reviews', 'accuracy_percentage')
    
    # Remove batch tracking columns from user_learning_sets
    op.drop_column('user_learning_sets', 'batch_size')
    op.drop_column('user_learning_sets', 'mastered_up_to')
    op.drop_column('user_learning_sets', 'isolation_phase')
    op.drop_column('user_learning_sets', 'current_batch_end')
    op.drop_column('user_learning_sets', 'current_batch_start')
