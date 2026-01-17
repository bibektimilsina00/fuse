"""Edit replace id integers in all models to use UUID instead

Revision ID: d98dd8ec85a3
Revises: 9c0a54914c78
Create Date: 2024-07-19 04:08:04.000976

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'd98dd8ec85a3'
down_revision = '9c0a54914c78'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Ensure uuid-ossp extension is available (Postgres only)
    if is_postgres:
        op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create a new UUID column with a default UUID value
    uuid_type = postgresql.UUID(as_uuid=True) if is_postgres else sa.String(36)
    uuid_default = sa.text('uuid_generate_v4()') if is_postgres else None

    op.add_column('user', sa.Column('new_id', uuid_type, default=uuid_default))
    op.add_column('item', sa.Column('new_id', uuid_type, default=uuid_default))
    op.add_column('item', sa.Column('new_owner_id', uuid_type, nullable=True))

    # Populate the new columns with UUIDs
    if is_postgres:
        op.execute('UPDATE "user" SET new_id = uuid_generate_v4()')
        op.execute('UPDATE item SET new_id = uuid_generate_v4()')
    else:
        # For SQLite, if we have data, we'd need to generate UUIDs here.
        # For new installs, the column is empty anyway.
        pass

    op.execute('UPDATE item SET new_owner_id = (SELECT new_id FROM "user" WHERE "user".id = item.owner_id)')

    # Set the new_id as not nullable and handle renaming/constraints in batch
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('new_id', nullable=False)
        batch_op.drop_column('id')
        batch_op.alter_column('new_id', new_column_name='id')
        batch_op.create_primary_key('user_pkey', ['id'])

    with op.batch_alter_table('item') as batch_op:
        batch_op.alter_column('new_id', nullable=False)
        if is_postgres:
            batch_op.drop_constraint('item_owner_id_fkey', type_='foreignkey')
        batch_op.drop_column('owner_id')
        batch_op.alter_column('new_owner_id', new_column_name='owner_id')
        batch_op.drop_column('id')
        batch_op.alter_column('new_id', new_column_name='id')
        batch_op.create_primary_key('item_pkey', ['id'])
        batch_op.create_foreign_key('item_owner_id_fkey', 'user', ['owner_id'], ['id'])

def downgrade():
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Reverse the upgrade process
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('old_id', sa.Integer, autoincrement=True))
    
    with op.batch_alter_table('item') as batch_op:
        batch_op.add_column(sa.Column('old_id', sa.Integer, autoincrement=True))
        batch_op.add_column(sa.Column('old_owner_id', sa.Integer, nullable=True))

    if is_postgres:
        op.execute('CREATE SEQUENCE IF NOT EXISTS user_id_seq AS INTEGER OWNED BY "user".old_id')
        op.execute('CREATE SEQUENCE IF NOT EXISTS item_id_seq AS INTEGER OWNED BY item.old_id')
        op.execute('SELECT setval(\'user_id_seq\', COALESCE((SELECT MAX(old_id) + 1 FROM "user"), 1), false)')
        op.execute('SELECT setval(\'item_id_seq\', COALESCE((SELECT MAX(old_id) + 1 FROM item), 1), false)')
        op.execute('UPDATE "user" SET old_id = nextval(\'user_id_seq\')')
        op.execute('UPDATE item SET old_id = nextval(\'item_id_seq\'), old_owner_id = (SELECT old_id FROM "user" WHERE "user".id = item.owner_id)')
    
    with op.batch_alter_table('item') as batch_op:
        if is_postgres:
            batch_op.drop_constraint('item_owner_id_fkey', type_='foreignkey')
        batch_op.drop_column('owner_id')
        batch_op.alter_column('old_owner_id', new_column_name='owner_id')
        batch_op.drop_column('id')
        batch_op.alter_column('old_id', new_column_name='id')
        batch_op.create_primary_key('item_pkey', ['id'])
        batch_op.create_foreign_key('item_owner_id_fkey', 'user', ['owner_id'], ['id'])

    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('id')
        batch_op.alter_column('old_id', new_column_name='id')
        batch_op.create_primary_key('user_pkey', ['id'])
