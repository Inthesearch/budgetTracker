from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime, date
from .models import TransactionType

# Base schemas
class BaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

# Category schemas
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = "#3B82F6"
    icon: Optional[str] = "📁"
    
    @validator('name')
    def convert_name_to_lowercase(cls, v):
        return v.lower()

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    name: Optional[str] = Field(None, min_length=1, max_length=100)

class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @validator('name', pre=True)
    def format_name_for_display(cls, v):
        from .utils import format_category_name
        return format_category_name(v)
    
    class Config:
        from_attributes = True

# SubCategory schemas
class SubCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    
    @validator('name')
    def convert_name_to_lowercase(cls, v):
        return v.lower()

class SubCategoryCreate(SubCategoryBase):
    category_id: int

class SubCategoryUpdate(SubCategoryBase):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category_id: Optional[int] = None

class SubCategoryResponse(SubCategoryBase):
    id: int
    user_id: int
    category_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @validator('name', pre=True)
    def format_name_for_display(cls, v):
        from .utils import format_subcategory_name
        return format_subcategory_name(v)
    
    class Config:
        from_attributes = True

# Account schemas
class AccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(default="bank", pattern="^(bank|credit|cash|investment)$")
    balance: float = Field(default=0.0, ge=0)
    currency: str = Field(default="USD", max_length=3)

    @validator('name')
    def convert_name_to_lowercase(cls, v):
        return v.lower()

class AccountCreate(AccountBase):
    pass

class AccountUpdate(AccountBase):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, pattern="^(bank|credit|cash|investment)$")
    balance: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)

class AccountResponse(AccountBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @validator('name', pre=True)
    def format_name_for_display(cls, v):
        from .utils import format_account_name
        return format_account_name(v)
    
    class Config:
        from_attributes = True

# Transaction schemas
class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0)
    type: TransactionType
    date: datetime
    notes: Optional[str] = None
    category_id: int
    sub_category_id: int
    account_id: int

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[TransactionType] = None
    date: Optional[datetime] = None
    notes: Optional[str] = None
    category_id: Optional[int] = None
    sub_category_id: Optional[int] = None
    account_id: Optional[int] = None

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Include related data
    category: Optional[CategoryResponse] = None
    sub_category: Optional[SubCategoryResponse] = None
    account: Optional[AccountResponse] = None
    
    class Config:
        from_attributes = True

# Filter and pagination schemas
class TransactionFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    type: Optional[TransactionType] = None
    category_id: Optional[int] = None
    sub_category_id: Optional[int] = None
    account_id: Optional[int] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None

# Dashboard schemas
class DashboardStats(BaseModel):
    total_income: float
    total_expense: float
    net_balance: float
    transaction_count: int
    top_categories: List[dict]
    recent_transactions: List[TransactionResponse]

# Error schemas
class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None 