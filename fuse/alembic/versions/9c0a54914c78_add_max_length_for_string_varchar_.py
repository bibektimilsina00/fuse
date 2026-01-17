"""Add max length for string(varchar) fields in User and Items models

Revision ID: 9c0a54914c78
Revises: e2412789c190
Create Date: 2024-06-17 14:42:44.639457

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '9c0a54914c78'
down_revision = 'e2412789c190'
branch_labels = None
depends_on = None


def upgrade():
    # Adjust the length of the email and full_name fields in the User table
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('email',
                   existing_type=sa.String(),
                   type_=sa.String(length=255),
                   existing_nullable=False)
        batch_op.alter_column('full_name',
                   existing_type=sa.String(),
                   type_=sa.String(length=255),
                   existing_nullable=True)

    # Adjust the length of the title and description fields in the Item table
    with op.batch_alter_table('item') as batch_op:
        batch_op.alter_column('title',
                   existing_type=sa.String(),
                   type_=sa.String(length=255),
                   existing_nullable=False)
        batch_op.alter_column('description',
                   existing_type=sa.String(),
                   type_=sa.String(length=255),
                   existing_nullable=True)


def downgrade():
    # Revert the length of the email and full_name fields in the User table
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('email',
                   existing_type=sa.String(length=255),
                   type_=sa.String(),
                   existing_nullable=False)
        batch_op.alter_column('full_name',
                   existing_type=sa.String(length=255),
                   type_=sa.String(),
                   existing_nullable=True)

    # Revert the length of the title and description fields in the Item table
    with op.batch_alter_table('item') as batch_op:
        batch_op.alter_column('title',
                   existing_type=sa.String(length=255),
                   type_=sa.String(),
                   existing_nullable=False)
        batch_op.alter_column('description',
                   existing_type=sa.String(length=255),
                   type_=sa.String(),
                   existing_nullable=True)
