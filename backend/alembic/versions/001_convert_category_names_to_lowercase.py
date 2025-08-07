"""convert category names to lowercase

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Convert existing category names to lowercase
    op.execute("UPDATE categories SET name = LOWER(name)")
    
    # Convert existing subcategory names to lowercase
    op.execute("UPDATE sub_categories SET name = LOWER(name)")


def downgrade():
    # Note: We can't easily restore the original case since we don't know what it was
    # This is a one-way migration
    pass
