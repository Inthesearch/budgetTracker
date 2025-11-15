"""convert category names to lowercase

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '001'
down_revision = '000'  # Depends on initial schema
branch_labels = None
depends_on = None


def upgrade():
    # Check if tables exist before trying to update them
    # This migration only runs if tables already have data
    connection = op.get_bind()
    inspector = inspect(connection)
    tables = inspector.get_table_names()
    
    # Check if categories table exists and has data
    if 'categories' in tables:
        try:
            result = connection.execute(sa.text("SELECT COUNT(*) FROM categories"))
            count = result.scalar()
            if count > 0:
                op.execute("UPDATE categories SET name = LOWER(name)")
        except Exception:
            # Table exists but might be empty or have issues, skip update
            pass
    
    # Check if sub_categories table exists and has data
    if 'sub_categories' in tables:
        try:
            result = connection.execute(sa.text("SELECT COUNT(*) FROM sub_categories"))
            count = result.scalar()
            if count > 0:
                op.execute("UPDATE sub_categories SET name = LOWER(name)")
        except Exception:
            # Table exists but might be empty or have issues, skip update
            pass


def downgrade():
    # Note: We can't easily restore the original case since we don't know what it was
    # This is a one-way migration
    pass
