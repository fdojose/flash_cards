"""Add integration tracking fields to user_element_reviews

Revision ID: add_integration_tracking
Revises: 
Create Date: 2025-08-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_integration_tracking'
down_revision = '9b5e8f2d7a1c'  # Point to the latest migration
branch_labels = None
depends_on = None

def upgrade():
    """Add integration tracking fields to user_element_reviews table"""
    # Add new columns with nullable=True first, then set defaults and make non-nullable
    op.add_column('user_element_reviews', 
        sa.Column('integration_confirmed', sa.Boolean(), nullable=True))
    op.add_column('user_element_reviews',
        sa.Column('integration_attempts', sa.Integer(), nullable=True))
    op.add_column('user_element_reviews',
        sa.Column('last_integration_attempt', sa.DateTime(), nullable=True))
    op.add_column('user_element_reviews',
        sa.Column('stability_score', sa.Float(), nullable=True))
    
    # Set default values for existing records
    op.execute("UPDATE user_element_reviews SET integration_confirmed = false WHERE integration_confirmed IS NULL")
    op.execute("UPDATE user_element_reviews SET integration_attempts = 0 WHERE integration_attempts IS NULL")
    op.execute("UPDATE user_element_reviews SET stability_score = 1.0 WHERE stability_score IS NULL")
    
    # Now make the columns non-nullable (except last_integration_attempt)
    op.alter_column('user_element_reviews', 'integration_confirmed', nullable=False, server_default='false')
    op.alter_column('user_element_reviews', 'integration_attempts', nullable=False, server_default='0')
    op.alter_column('user_element_reviews', 'stability_score', nullable=False, server_default='1.0')
    
    print("✅ Integration tracking fields added successfully")

def downgrade():
    """Remove integration tracking fields"""
    op.drop_column('user_element_reviews', 'stability_score')
    op.drop_column('user_element_reviews', 'last_integration_attempt')
    op.drop_column('user_element_reviews', 'integration_attempts')
    op.drop_column('user_element_reviews', 'integration_confirmed')
    
    print("✅ Integration tracking fields removed successfully")
