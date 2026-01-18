"""Add spec column to WorkflowNode and remove config

Revision ID: 82e10e9b2e3f
Revises: ceedbe88ef0d
Create Date: 2025-12-22 16:16:07.112539

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '82e10e9b2e3f'
down_revision = 'ceedbe88ef0d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('workflow_nodes', sa.Column('spec', sa.JSON(), nullable=True))
    # Fill existing rows with empty dict if they exist
    op.execute("UPDATE workflow_nodes SET spec = '{}'")
    
    with op.batch_alter_table('workflow_nodes', schema=None) as batch_op:
        batch_op.alter_column('spec', nullable=False)
        batch_op.drop_column('config')


def downgrade():
    with op.batch_alter_table('workflow_nodes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('config', sa.VARCHAR(), autoincrement=False, nullable=True))
        batch_op.drop_column('spec')
