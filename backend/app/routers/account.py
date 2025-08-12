from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, Account
from ..schemas import AccountCreate, AccountUpdate, AccountResponse, BaseResponse
from ..auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter(prefix="/account", tags=["Accounts"])

@router.post("/addAccount", response_model=BaseResponse)
async def add_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a new account."""
    # Check if account name already exists for this user (case-insensitive)
    existing_account = await db.execute(select(Account).where(
        Account.name == account_data.name.lower(),
        Account.user_id == current_user.id,
        Account.is_active == True
    ))
    existing_account = existing_account.scalars().first()
    
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account name already exists"
        )
    
    # Create new account
    db_account = Account(
        name=account_data.name,
        type=account_data.type,
        balance=account_data.balance,
        currency=account_data.currency,
        user_id=current_user.id
    )
    
    db.add(db_account)
    await db.commit()
    await db.refresh(db_account)
    
    return BaseResponse(
        success=True,
        message="Account added successfully",
        data={"account_id": db_account.id}
    )

@router.put("/editAccount/{account_id}", response_model=BaseResponse)
async def edit_account(
    account_id: int,
    account_data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Edit an existing account."""
    # Find account
    account = await db.execute(select(Account).where(
        Account.id == account_id,
        Account.user_id == current_user.id,
        Account.is_active == True
    ))
    account = account.scalars().first()
    

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Check if new name conflicts with existing account (case-insensitive)
    if account_data.name and account_data.name.lower() != account.name:
        existing_account = await db.execute(select(Account).where(
            Account.name == account_data.name.lower(),
            Account.user_id == current_user.id,
            Account.is_active == True,
            Account.id != account_id
        ))
        existing_account = existing_account.scalars().first()
        
        if existing_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account name already exists"
            )
    
    # Update account
    if account_data.name is not None:
        account.name = account_data.name.lower()
    if account_data.type is not None:
        account.type = account_data.type
    if account_data.balance is not None:
        account.balance = account_data.balance
    if account_data.currency is not None:
        account.currency = account_data.currency
    
    await db.commit()
    await db.refresh(account)
    
    return BaseResponse(
        success=True,
        message="Account updated successfully"
    )

@router.put("/deleteAccount/{account_id}", response_model=BaseResponse)
async def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete an account."""
    # Find account
    account = await db.execute(select(Account).where(
        Account.id == account_id,
        Account.user_id == current_user.id,
        Account.is_active == True
    ))
    account = account.scalars().first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Check if account has active transactions
    from ..models import Transaction
    active_transactions = await db.execute(select(Transaction).where(
        Transaction.account_id == account_id,
        Transaction.is_active == True
    ))
    active_transactions = active_transactions.scalars().first()
    
    if active_transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete account with active transactions"
        )
    
    # Soft delete account
    account.is_active = False
    await db.commit()
    
    return BaseResponse(
        success=True,
        message="Account deleted successfully"
    )

@router.get("/list", response_model=List[AccountResponse])
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    print("Listing accounts", current_user.id)
    """Get all active accounts for the current user."""
    accounts = await db.execute(select(Account).where(
        Account.user_id == current_user.id,
        Account.is_active == True
    ))
    accounts = accounts.scalars().all()
    
    return accounts

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account_detail(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific account."""
    account = await db.execute(select(Account).where(
        Account.id == account_id,
        Account.user_id == current_user.id,
        Account.is_active == True
    ))
    account = account.scalars().first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return account 