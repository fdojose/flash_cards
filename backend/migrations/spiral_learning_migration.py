"""Add spiral learning fields to UserLearningSet

Revision ID: spiral_learning_001
Revises: 
Create Date: 2025-08-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = 'spiral_learning_001'
down_revision = None  # Replace with actual last revision if using Alembic
branch_labels = None
depends_on = None


def upgrade():
    """Add spiral learning fields to user_learning_sets table"""
    op.add_column('user_learning_sets', 
                  sa.Column('completed_integration_cycles', sa.Integer(), default=0))
    op.add_column('user_learning_sets', 
                  sa.Column('spiral_review_mode', sa.Boolean(), default=False))
    op.add_column('user_learning_sets', 
                  sa.Column('last_spiral_review', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    """Remove spiral learning fields from user_learning_sets table"""
    op.drop_column('user_learning_sets', 'last_spiral_review')
    op.drop_column('user_learning_sets', 'spiral_review_mode')
    op.drop_column('user_learning_sets', 'completed_integration_cycles')
