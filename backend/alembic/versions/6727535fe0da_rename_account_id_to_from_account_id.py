"""rename_account_id_to_from_account_id

Revision ID: 6727535fe0da
Revises: 002
Create Date: 2025-08-11 19:49:01.064316

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '6727535fe0da'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if account_id exists (old schema) or from_account_id already exists (new schema)
    connection = op.get_bind()
    inspector = inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('transactions')]
    
    if 'account_id' in columns and 'from_account_id' not in columns:
        # Rename account_id to from_account_id (old database)
        op.alter_column('transactions', 'account_id', new_column_name='from_account_id')
    # If from_account_id already exists, skip (already in initial schema)


def downgrade() -> None:
    # Rename from_account_id back to account_id
    op.alter_column('transactions', 'from_account_id', new_column_name='account_id') 