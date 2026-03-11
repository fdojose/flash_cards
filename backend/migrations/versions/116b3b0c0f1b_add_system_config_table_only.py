"""add system config table only

Revision ID: 116b3b0c0f1b
Revises: 1cc02ea53d56
Create Date: 2025-08-03 23:02:35.158508

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '116b3b0c0f1b'
down_revision: Union[str, None] = '1cc02ea53d56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create system_configs table
    op.create_table('system_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('value_type', sa.String(length=20), nullable=False, server_default='string'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='general'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_configs_id'), 'system_configs', ['id'], unique=False)
    op.create_index(op.f('ix_system_configs_key'), 'system_configs', ['key'], unique=True)


def downgrade() -> None:
    # Drop system_configs table
    op.drop_index(op.f('ix_system_configs_key'), table_name='system_configs')
    op.drop_index(op.f('ix_system_configs_id'), table_name='system_configs')
    op.drop_table('system_configs')
