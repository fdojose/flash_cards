"""Fix Boolean column types in gamification and dashboard models

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-11 00:00:00.000000

Fixes columns that were incorrectly typed as String(10) instead of Boolean:
  - badge_definitions.is_active
  - weekly_goals.goal_achieved
  - learning_insights.is_read
  - learning_insights.is_actionable
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # badge_definitions.is_active: String(10) -> Boolean
    op.alter_column(
        'badge_definitions', 'is_active',
        existing_type=sa.String(10),
        type_=sa.Boolean(),
        existing_nullable=True,
        postgresql_using="CASE WHEN is_active IN ('true','True','1','yes') THEN TRUE ELSE FALSE END"
    )

    # weekly_goals.goal_achieved: String(10) -> Boolean
    op.alter_column(
        'weekly_goals', 'goal_achieved',
        existing_type=sa.String(10),
        type_=sa.Boolean(),
        existing_nullable=True,
        postgresql_using="CASE WHEN goal_achieved IN ('true','True','1','yes') THEN TRUE ELSE FALSE END"
    )

    # learning_insights.is_read: String(10) -> Boolean
    op.alter_column(
        'learning_insights', 'is_read',
        existing_type=sa.String(10),
        type_=sa.Boolean(),
        existing_nullable=True,
        postgresql_using="CASE WHEN is_read IN ('true','True','1','yes') THEN TRUE ELSE FALSE END"
    )

    # learning_insights.is_actionable: String(10) -> Boolean
    op.alter_column(
        'learning_insights', 'is_actionable',
        existing_type=sa.String(10),
        type_=sa.Boolean(),
        existing_nullable=True,
        postgresql_using="CASE WHEN is_actionable IN ('true','True','1','yes') THEN TRUE ELSE FALSE END"
    )


def downgrade():
    op.alter_column(
        'badge_definitions', 'is_active',
        existing_type=sa.Boolean(),
        type_=sa.String(10),
        existing_nullable=True
    )
    op.alter_column(
        'weekly_goals', 'goal_achieved',
        existing_type=sa.Boolean(),
        type_=sa.String(10),
        existing_nullable=True
    )
    op.alter_column(
        'learning_insights', 'is_read',
        existing_type=sa.Boolean(),
        type_=sa.String(10),
        existing_nullable=True
    )
    op.alter_column(
        'learning_insights', 'is_actionable',
        existing_type=sa.Boolean(),
        type_=sa.String(10),
        existing_nullable=True
    )
