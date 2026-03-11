"""Add FSRS difficulty and desired_retention fields

Revision ID: a1b2c3d4e5f6
Revises: add_integration_tracking
Create Date: 2026-03-11 00:00:00.000000

Adds two columns required for the full FSRS 4.5 algorithm:
  - user_element_reviews.difficulty   (float, default 5.0)
  - spaced_repetition_configs.desired_retention  (float, default 0.9)
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'add_integration_tracking'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # FSRS difficulty per card (D, scale 1–10)
    op.add_column(
        'user_element_reviews',
        sa.Column('difficulty', sa.Float(), nullable=True)
    )
    op.execute("UPDATE user_element_reviews SET difficulty = 5.0 WHERE difficulty IS NULL")
    op.alter_column('user_element_reviews', 'difficulty',
                    nullable=False, server_default='5.0')

    # Desired retention per user config (R, 0.8–0.95)
    op.add_column(
        'spaced_repetition_configs',
        sa.Column('desired_retention', sa.Float(), nullable=True)
    )
    op.execute(
        "UPDATE spaced_repetition_configs SET desired_retention = 0.9 "
        "WHERE desired_retention IS NULL"
    )
    op.alter_column('spaced_repetition_configs', 'desired_retention',
                    nullable=False, server_default='0.9')

    # Flip default algorithm to fsrs for new rows
    op.alter_column('spaced_repetition_configs', 'algorithm',
                    server_default='fsrs')


def downgrade() -> None:
    op.alter_column('spaced_repetition_configs', 'algorithm',
                    server_default='sm2')
    op.drop_column('spaced_repetition_configs', 'desired_retention')
    op.drop_column('user_element_reviews', 'difficulty')
