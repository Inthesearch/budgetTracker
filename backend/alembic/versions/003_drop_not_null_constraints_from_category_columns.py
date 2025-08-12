"""drop_not_null_constraints_from_category_columns

Revision ID: 003
Revises: 6727535fe0da
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '6727535fe0da'
branch_labels = None
depends_on = None


def upgrade():
    # Drop NOT NULL constraints from category_id and sub_category_id
    # This allows transfer transactions to have NULL categories
    op.alter_column('transactions', 'category_id', nullable=True)
    op.alter_column('transactions', 'sub_category_id', nullable=True)


def downgrade():
    # Restore NOT NULL constraints (but this might fail if there are existing NULL values)
    # Note: This downgrade will fail if there are any transfer transactions with NULL categories
    op.alter_column('transactions', 'category_id', nullable=False)
    op.alter_column('transactions', 'sub_category_id', nullable=False)
