"""create_dataset_models

Revision ID: 1cc02ea53d56
Revises: 530620d2eba3
Create Date: 2025-08-03 00:07:55.254753

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '1cc02ea53d56'
down_revision: Union[str, None] = '530620d2eba3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create datasets table
    op.create_table(
        'datasets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create index on name for faster searches
    op.create_index('idx_datasets_name', 'datasets', ['name'])
    
    # Create elements table
    op.create_table(
        'elements',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_id', UUID(as_uuid=True), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create indexes for elements
    op.create_index('idx_elements_dataset_id', 'elements', ['dataset_id'])
    op.create_index('idx_elements_code', 'elements', ['code'])
    
    # Create fields table
    op.create_table(
        'fields',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('element_id', UUID(as_uuid=True), sa.ForeignKey('elements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('field_name', sa.String(255), nullable=False),
        sa.Column('field_value', sa.Text(), nullable=False),
        sa.Column('field_type', sa.String(50), nullable=False, server_default='text'),
        sa.Column('media_url', sa.Text(), nullable=True),
    )
    
    # Create indexes for fields
    op.create_index('idx_fields_element_id', 'fields', ['element_id'])
    op.create_index('idx_fields_name', 'fields', ['field_name'])
    op.create_index('idx_fields_type', 'fields', ['field_type'])
    
    # Create tags table (optional for categorization)
    op.create_table(
        'tags',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create index on tag name
    op.create_index('idx_tags_name', 'tags', ['name'])
    
    # Create element_tags junction table
    op.create_table(
        'element_tags',
        sa.Column('element_id', UUID(as_uuid=True), sa.ForeignKey('elements.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', UUID(as_uuid=True), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    )


def downgrade() -> None:
    # Drop tables in reverse order to avoid foreign key constraints
    op.drop_table('element_tags')
    op.drop_table('tags')
    op.drop_table('fields')
    op.drop_table('elements')
    op.drop_table('datasets')
