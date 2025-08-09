from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from datetime import datetime, date

from ..database import get_db
from ..models import User, Transaction, Category, SubCategory, Account
from ..schemas import (
    TransactionCreate, TransactionUpdate, TransactionResponse, 
    TransactionFilter, PaginationParams, BaseResponse
)
from ..auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter(prefix="/transaction", tags=["Transactions"])

@router.post("/addTransaction", response_model=BaseResponse)
async def add_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a new transaction and apply its effect to the account balance."""
    # Verify account exists and belongs to user
    account = await db.execute(select(Account).where(
        Account.id == transaction_data.account_id,
        Account.user_id == current_user.id,
        Account.is_active == True
    ))
    account = account.scalars().first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Verify category if provided
    if transaction_data.category_id:
        category = await db.execute(select(Category).where(
            Category.id == transaction_data.category_id,
            Category.user_id == current_user.id,
            Category.is_active == True
        ))
        category = category.scalars().first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
    
    # Verify sub-category if provided
    if transaction_data.sub_category_id:
        sub_category = await db.execute(select(SubCategory).where(
            SubCategory.id == transaction_data.sub_category_id,
            SubCategory.user_id == current_user.id,
            SubCategory.is_active == True
        ))
        sub_category = sub_category.scalars().first()
        
        if not sub_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sub-category not found"
            )
        
        # Verify sub-category belongs to the specified category
        if transaction_data.category_id and sub_category.category_id != transaction_data.category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sub-category does not belong to the specified category"
            )
    
    # Create transaction
    db_transaction = Transaction(
        amount=transaction_data.amount,
        type=transaction_data.type,
        date=transaction_data.date,
        notes=transaction_data.notes,
        category_id=transaction_data.category_id,
        sub_category_id=transaction_data.sub_category_id,
        account_id=transaction_data.account_id,
        user_id=current_user.id
    )
    db.add(db_transaction)

    # Apply balance side-effect
    # Note: For Option B (transfer as two transactions), we only handle income/expense here
    if str(transaction_data.type) == "income":
        account.balance = (account.balance or 0) + transaction_data.amount
    elif str(transaction_data.type) == "expense":
        account.balance = (account.balance or 0) - transaction_data.amount

    await db.commit()
    await db.refresh(db_transaction)
    
    return BaseResponse(
        success=True,
        message="Transaction added successfully",
        data={"transaction_id": db_transaction.id}
    )

@router.put("/editTransaction/{transaction_id}", response_model=BaseResponse)
async def edit_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Edit-as-new: deactivate the old transaction, reverse its effect, then create a new one and apply its effect."""
    # Find transaction
    transaction = await db.execute(select(Transaction).where(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
        Transaction.is_active == True
    ))
    transaction = transaction.scalars().first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Verify account if provided
    if transaction_data.account_id:
        account = await db.execute(select(Account).where(
            Account.id == transaction_data.account_id,
            Account.user_id == current_user.id,
            Account.is_active == True
        ))
        account = account.scalars().first()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
    
    # Verify category if provided
    if transaction_data.category_id:
        category = await db.execute(select(Category).where(
            Category.id == transaction_data.category_id,
            Category.user_id == current_user.id,
            Category.is_active == True
        ))
        category = category.scalars().first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
    
    # Verify sub-category if provided
    if transaction_data.sub_category_id:
        sub_category = await db.execute(select(SubCategory).where(
            SubCategory.id == transaction_data.sub_category_id,
            SubCategory.user_id == current_user.id,
            SubCategory.is_active == True
        ))
        sub_category = sub_category.scalars().first()
        
        if not sub_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sub-category not found"
            )
        
        # Verify sub-category belongs to the specified category
        if transaction_data.category_id and sub_category.category_id != transaction_data.category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sub-category does not belong to the specified category"
            )
    
    # Reverse old balance effect
    old_account = await db.execute(select(Account).where(
        Account.id == transaction.account_id,
        Account.user_id == current_user.id,
        Account.is_active == True
    ))
    old_account = old_account.scalars().first()

    if old_account:
        if str(transaction.type) == "income":
            old_account.balance = (old_account.balance or 0) - transaction.amount
        elif str(transaction.type) == "expense":
            old_account.balance = (old_account.balance or 0) + transaction.amount

    # Deactivate old transaction
    transaction.is_active = False

    # Build new transaction using provided fields overriding old
    new_amount = transaction_data.amount if transaction_data.amount is not None else transaction.amount
    new_type = transaction_data.type if transaction_data.type is not None else transaction.type
    new_date = transaction_data.date if transaction_data.date is not None else transaction.date
    new_notes = transaction_data.notes if transaction_data.notes is not None else transaction.notes
    new_category_id = transaction_data.category_id if transaction_data.category_id is not None else transaction.category_id
    new_sub_category_id = transaction_data.sub_category_id if transaction_data.sub_category_id is not None else transaction.sub_category_id
    new_account_id = transaction_data.account_id if transaction_data.account_id is not None else transaction.account_id

    # Verify new account exists
    new_account = await db.execute(select(Account).where(
        Account.id == new_account_id,
        Account.user_id == current_user.id,
        Account.is_active == True
    ))
    new_account = new_account.scalars().first()
    if not new_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    new_transaction = Transaction(
        amount=new_amount,
        type=new_type,
        date=new_date,
        notes=new_notes,
        category_id=new_category_id,
        sub_category_id=new_sub_category_id,
        account_id=new_account_id,
        user_id=current_user.id
    )
    db.add(new_transaction)

    # Apply new balance effect
    if str(new_type) == "income":
        new_account.balance = (new_account.balance or 0) + new_amount
    elif str(new_type) == "expense":
        new_account.balance = (new_account.balance or 0) - new_amount

    await db.commit()
    
    return BaseResponse(
        success=True,
        message="Transaction updated successfully"
    )

@router.put("/deleteTransaction/{transaction_id}", response_model=BaseResponse)
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a transaction and reverse its balance effect."""
    # Find transaction
    transaction = await db.execute(select(Transaction).where(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
        Transaction.is_active == True
    ))
    transaction = transaction.scalars().first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Reverse balance effect
    account = await db.execute(select(Account).where(
        Account.id == transaction.account_id,
        Account.user_id == current_user.id,
        Account.is_active == True
    ))
    account = account.scalars().first()

    if account:
        if str(transaction.type) == "income":
            account.balance = (account.balance or 0) - transaction.amount
        elif str(transaction.type) == "expense":
            account.balance = (account.balance or 0) + transaction.amount

    # Soft delete transaction
    transaction.is_active = False
    await db.commit()
    
    return BaseResponse(
        success=True,
        message="Transaction deleted successfully"
    )

@router.get("/getTransactionRecord", response_model=List[TransactionResponse])
async def get_transaction_record(
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    transaction_type: Optional[str] = Query(None, description="Transaction type (income/expense/transfer)"),
    category_id: Optional[int] = Query(None, description="Category ID for filtering"),
    sub_category_id: Optional[int] = Query(None, description="Sub-category ID for filtering"),
    account_id: Optional[int] = Query(None, description="Account ID for filtering"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(None, ge=1, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get transaction records with filtering and pagination."""
    try:
        # Build base query with related data
        stmt = select(Transaction).options(
            selectinload(Transaction.category),
            selectinload(Transaction.sub_category),
            selectinload(Transaction.account)
        ).where(
            Transaction.user_id == current_user.id,
            Transaction.is_active == True
        )
        
        # Apply filters
        if start_date:
            stmt = stmt.where(Transaction.date >= start_date)
        if end_date:
            stmt = stmt.where(Transaction.date <= end_date)
        if transaction_type:
            stmt = stmt.where(Transaction.type == transaction_type)
        if category_id:
            stmt = stmt.where(Transaction.category_id == category_id)
        if sub_category_id:
            stmt = stmt.where(Transaction.sub_category_id == sub_category_id)
        if account_id:
            stmt = stmt.where(Transaction.account_id == account_id)
        if min_amount is not None:
            stmt = stmt.where(Transaction.amount >= min_amount)
        if max_amount is not None:
            stmt = stmt.where(Transaction.amount <= max_amount)
        
        # Order by date descending (newest first)
        stmt = stmt.order_by(Transaction.date.desc())
        
        # Apply pagination
        if size:
            offset = (page - 1) * size
            stmt = stmt.offset(offset).limit(size)
        
        # Execute query
        result = await db.execute(stmt)
        transactions = result.scalars().all()
        
        return transactions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transactions: {str(e)}"
        )

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_detail(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific transaction."""
    try:
        # Use select with options to load related data
        stmt = select(Transaction).options(
            selectinload(Transaction.category),
            selectinload(Transaction.sub_category),
            selectinload(Transaction.account)
        ).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
            Transaction.is_active == True
        )
        
        result = await db.execute(stmt)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transaction: {str(e)}"
        ) 