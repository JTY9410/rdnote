"""Add approval_stage and file_hash

Revision ID: 0002
Revises: 0001
Create Date: 2025-10-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add approval_stage to research_notes
    op.add_column('research_notes', sa.Column('approval_stage', sa.String(20), nullable=False, server_default='DRAFT'))
    
    # Add file_hash to files
    op.add_column('files', sa.Column('file_hash', sa.String(64), nullable=True))
    
    # Add indexes for better performance
    op.create_index('ix_research_notes_approval_stage', 'research_notes', ['approval_stage'])


def downgrade() -> None:
    op.drop_index('ix_research_notes_approval_stage', table_name='research_notes')
    op.drop_column('files', 'file_hash')
    op.drop_column('research_notes', 'approval_stage')

