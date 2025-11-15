"""add to_account_id to transactions table

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Check if to_account_id column already exists (might be in initial schema)
    connection = op.get_bind()
    inspector = inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('transactions')]
    
    if 'to_account_id' not in columns:
        # Add to_account_id column to transactions table
        op.add_column('transactions', sa.Column('to_account_id', sa.Integer(), nullable=True))
        
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_transactions_to_account_id_accounts',
            'transactions', 'accounts',
            ['to_account_id'], ['id']
        )


def downgrade():
    # Remove foreign key constraint
    op.drop_constraint('fk_transactions_to_account_id_accounts', 'transactions', type_='foreignkey')
    
    # Remove to_account_id column
    op.drop_column('transactions', 'to_account_id')
