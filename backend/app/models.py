from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from .database import Base
import enum

class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    sub_categories = relationship("SubCategory", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    color = Column(String, default="#3B82F6")  # Default blue color
    icon = Column(String, default="📁")  # Default icon
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="categories")
    sub_categories = relationship("SubCategory", back_populates="category", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="category")
    
    def __init__(self, **kwargs):
        # Convert name to lowercase before saving
        if 'name' in kwargs:
            kwargs['name'] = kwargs['name'].lower()
        super().__init__(**kwargs)

class SubCategory(Base):
    __tablename__ = "sub_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sub_categories")
    category = relationship("Category", back_populates="sub_categories")
    transactions = relationship("Transaction", back_populates="sub_category")
    
    def __init__(self, **kwargs):
        # Convert name to lowercase before saving
        if 'name' in kwargs:
            kwargs['name'] = kwargs['name'].lower()
        super().__init__(**kwargs)

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, default="bank")  # bank, credit, cash, investment
    balance = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    # Outgoing transactions (money leaving this account)
    transactions_from = relationship(
        "Transaction",
        back_populates="from_account",
        foreign_keys="[Transaction.from_account_id]"
    )

    # Incoming transactions (money going into this account)
    transactions_to = relationship(
        "Transaction",
        back_populates="to_account",
        foreign_keys="[Transaction.to_account_id]"
    )


    def __init__(self, **kwargs):
        # Convert name to lowercase before saving
        if 'name' in kwargs:
            kwargs['name'] = kwargs['name'].lower()
        super().__init__(**kwargs)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  # Nullable for transfers
    sub_category_id = Column(Integer, ForeignKey("sub_categories.id"), nullable=True)  # Nullable for transfers
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)  # For transfer transactions
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    sub_category = relationship("SubCategory", back_populates="transactions")
    from_account = relationship(
        "Account",
        back_populates="transactions_from",
        foreign_keys=[from_account_id]
    )

    to_account = relationship(
        "Account",
        back_populates="transactions_to",
        foreign_keys=[to_account_id]
    )


class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 