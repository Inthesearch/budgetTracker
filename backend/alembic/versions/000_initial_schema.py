"""Initial schema - create all tables

Revision ID: 000
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # For PostgreSQL, ensure enum type exists before creating tables
    connection = op.get_bind()
    if connection.dialect.name == 'postgresql':
        # Create enum type only if it doesn't exist using DO block
        connection.execute(sa.text("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transactiontype') THEN
                    CREATE TYPE transactiontype AS ENUM ('income', 'expense', 'transfer');
                END IF;
            END $$;
        """))
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(), nullable=True, server_default='#3B82F6'),
        sa.Column('icon', sa.String(), nullable=True, server_default='📁'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_categories_id'), 'categories', ['id'], unique=False)

    # Create sub_categories table
    op.create_table(
        'sub_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sub_categories_id'), 'sub_categories', ['id'], unique=False)

    # Create accounts table
    op.create_table(
        'accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=True, server_default='bank'),
        sa.Column('balance', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('currency', sa.String(), nullable=True, server_default='USD'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accounts_id'), 'accounts', ['id'], unique=False)

    # Create transactions table
    # Note: We'll create it with from_account_id and to_account_id from the start
    # to match the current model structure
    # Handle enum differently for PostgreSQL vs SQLite
    if connection.dialect.name == 'postgresql':
        # Create table without the enum column first, then add it with ALTER TABLE
        # This bypasses SQLAlchemy's enum creation mechanism
        op.create_table(
            'transactions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=True),
            sa.Column('sub_category_id', sa.Integer(), nullable=True),
            sa.Column('from_account_id', sa.Integer(), nullable=False),
            sa.Column('to_account_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
            sa.ForeignKeyConstraint(['sub_category_id'], ['sub_categories.id'], ),
            sa.ForeignKeyConstraint(['from_account_id'], ['accounts.id'], ),
            sa.ForeignKeyConstraint(['to_account_id'], ['accounts.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
        
        # Now add the enum column using raw SQL to avoid SQLAlchemy's enum creation
        op.execute("ALTER TABLE transactions ADD COLUMN type transactiontype NOT NULL")
    else:
        # SQLite doesn't support enums, use String instead
        op.create_table(
            'transactions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('type', sa.String(), nullable=False),
            sa.Column('date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=True),
            sa.Column('sub_category_id', sa.Integer(), nullable=True),
            sa.Column('from_account_id', sa.Integer(), nullable=False),
            sa.Column('to_account_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
            sa.ForeignKeyConstraint(['sub_category_id'], ['sub_categories.id'], ),
            sa.ForeignKeyConstraint(['from_account_id'], ['accounts.id'], ),
            sa.ForeignKeyConstraint(['to_account_id'], ['accounts.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)

    # Create password_resets table
    op.create_table(
        'password_resets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_resets_token'), 'password_resets', ['token'], unique=True)


def downgrade():
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('password_resets')
    op.drop_table('transactions')
    op.drop_table('accounts')
    op.drop_table('sub_categories')
    op.drop_table('categories')
    op.drop_table('users')
    
    # Drop the enum type (PostgreSQL only)
    connection = op.get_bind()
    if connection.dialect.name == 'postgresql':
        op.execute("DROP TYPE IF EXISTS transactiontype")

