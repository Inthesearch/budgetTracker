from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from datetime import datetime, date
import pandas as pd
import io
import asyncio
from sqlalchemy import and_, func

from ..database import get_db
from ..models import User, Transaction, Category, SubCategory, Account, TransactionType
from ..schemas import (
    TransactionCreate, TransactionUpdate, TransactionResponse, 
    TransactionFilter, PaginationParams, BaseResponse, DashboardStats
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
        Account.id == transaction_data.from_account_id,
        Account.user_id == current_user.id,
        Account.is_active == True
    ))
    account = account.scalars().first()

    print("transaction_data", transaction_data)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Handle transfer transactions
    if transaction_data.type == TransactionType.TRANSFER:
        # Validate to_account_id is provided for transfers
        if not transaction_data.to_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="to_account_id is required for transfer transactions"
            )
        
        # Verify to_account exists and belongs to user
        to_account = await db.execute(select(Account).where(
            Account.id == transaction_data.to_account_id,
            Account.user_id == current_user.id,
            Account.is_active == True
        ))
        to_account = to_account.scalars().first()
        
        if not to_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="To account not found"
            )
        
        # Ensure from and to accounts are different
        if transaction_data.from_account_id == transaction_data.to_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="From and to accounts must be different"
            )
        
        # For transfers, category and sub_category should be null
        if transaction_data.category_id or transaction_data.sub_category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category and sub-category should not be set for transfer transactions"
            )
    
    # Handle income/expense transactions
    else:
        # Validate to_account_id is not provided for non-transfer transactions
        if transaction_data.to_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="to_account_id should not be set for income/expense transactions"
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
    # The TransactionTypeEnum TypeDecorator will automatically convert enum to lowercase value
    db_transaction = Transaction(
        amount=transaction_data.amount,
        type=transaction_data.type,  # TypeDecorator handles conversion to lowercase
        date=transaction_data.date,
        notes=transaction_data.notes,
        category_id=transaction_data.category_id,
        sub_category_id=transaction_data.sub_category_id,
        from_account_id=transaction_data.from_account_id,
        to_account_id=transaction_data.to_account_id,
        user_id=current_user.id
    )
    db.add(db_transaction)

    # Apply balance side-effect
    if transaction_data.type == TransactionType.INCOME:
        account.balance = (account.balance or 0) + transaction_data.amount
    elif transaction_data.type == TransactionType.EXPENSE:
        account.balance = (account.balance or 0) - transaction_data.amount
    elif transaction_data.type == TransactionType.TRANSFER:
        # For transfers, decrease from account and increase to account
        account.balance = (account.balance or 0) - transaction_data.amount
        to_account.balance = (to_account.balance or 0) + transaction_data.amount

    await db.commit()
    await db.refresh(db_transaction)
    
    # Refresh accounts to get updated balances
    await db.refresh(account)
    if transaction_data.type == TransactionType.TRANSFER:
        await db.refresh(to_account)
    
    # Calculate total available funds (sum of all account balances)
    all_accounts_result = await db.execute(
        select(Account).where(
            Account.user_id == current_user.id,
            Account.is_active == True
        )
    )
    all_accounts = all_accounts_result.scalars().all()
    total_available_funds = sum(acc.balance or 0 for acc in all_accounts)
    
    # Prepare response data with updated balances
    response_data = {
        "transaction_id": db_transaction.id,
        "from_account": {
            "id": account.id,
            "name": account.name,
            "balance": account.balance
        },
        "total_available_funds": total_available_funds
    }
    
    # Include to_account for transfers
    if transaction_data.type == TransactionType.TRANSFER:
        response_data["to_account"] = {
            "id": to_account.id,
            "name": to_account.name,
            "balance": to_account.balance
        }
    
    return BaseResponse(
        success=True,
        message="Transaction added successfully",
        data=response_data
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
    if transaction_data.from_account_id:
        account = await db.execute(select(Account).where(
            Account.id == transaction_data.from_account_id,
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
        Account.id == transaction.from_account_id,
        Account.user_id == current_user.id,
        Account.is_active == True
    ))
    old_account = old_account.scalars().first()

    if old_account:
        if str(transaction.type) == "income":
            old_account.balance = (old_account.balance or 0) - transaction.amount
        elif str(transaction.type) == "expense":
            old_account.balance = (old_account.balance or 0) + transaction.amount
        elif str(transaction.type) == "transfer":
            # For transfers, reverse both accounts
            old_account.balance = (old_account.balance or 0) + transaction.amount
            
            # Also reverse the to_account if it exists
            if transaction.to_account_id:
                old_to_account = await db.execute(select(Account).where(
                    Account.id == transaction.to_account_id,
                    Account.user_id == current_user.id,
                    Account.is_active == True
                ))
                old_to_account = old_to_account.scalars().first()
                if old_to_account:
                    old_to_account.balance = (old_to_account.balance or 0) - transaction.amount

    # Deactivate old transaction
    transaction.is_active = False

    # Build new transaction using provided fields overriding old
    new_amount = transaction_data.amount if transaction_data.amount is not None else transaction.amount
    new_type = transaction_data.type if transaction_data.type is not None else transaction.type
    new_date = transaction_data.date if transaction_data.date is not None else transaction.date
    new_notes = transaction_data.notes if transaction_data.notes is not None else transaction.notes
    new_category_id = transaction_data.category_id if transaction_data.category_id is not None else transaction.category_id
    new_sub_category_id = transaction_data.sub_category_id if transaction_data.sub_category_id is not None else transaction.sub_category_id
    new_account_id = transaction_data.from_account_id if transaction_data.from_account_id is not None else transaction.from_account_id
    new_to_account_id = transaction_data.to_account_id if transaction_data.to_account_id is not None else transaction.to_account_id

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

    # Verify to_account for transfers
    new_to_account = None
    if new_type == TransactionType.TRANSFER:
        if not new_to_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="to_account_id is required for transfer transactions"
            )
        
        new_to_account = await db.execute(select(Account).where(
            Account.id == new_to_account_id,
            Account.user_id == current_user.id,
            Account.is_active == True
        ))
        new_to_account = new_to_account.scalars().first()
        
        if not new_to_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="To account not found"
            )
        
        # Ensure from and to accounts are different
        if new_account_id == new_to_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="From and to accounts must be different"
            )

    new_transaction = Transaction(
        amount=new_amount,
        type=new_type,
        date=new_date,
        notes=new_notes,
        category_id=new_category_id,
        sub_category_id=new_sub_category_id,
        from_account_id=new_account_id,
        to_account_id=new_to_account_id,
        user_id=current_user.id
    )
    db.add(new_transaction)

    # Apply new balance effect
    if str(new_type) == "income":
        new_account.balance = (new_account.balance or 0) + new_amount
    elif str(new_type) == "expense":
        new_account.balance = (new_account.balance or 0) - new_amount
    elif str(new_type) == "transfer":
        # For transfers, decrease from account and increase to account
        new_account.balance = (new_account.balance or 0) - new_amount
        new_to_account.balance = (new_to_account.balance or 0) + new_amount

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
        Account.id == transaction.from_account_id,
        Account.user_id == current_user.id,
        Account.is_active == True
    ))
    account = account.scalars().first()

    if account:
        if str(transaction.type) == "income":
            account.balance = (account.balance or 0) - transaction.amount
        elif str(transaction.type) == "expense":
            account.balance = (account.balance or 0) + transaction.amount
        elif str(transaction.type) == "transfer":
            # For transfers, reverse both accounts
            account.balance = (account.balance or 0) + transaction.amount
            
            # Also reverse the to_account if it exists
            if transaction.to_account_id:
                to_account = await db.execute(select(Account).where(
                    Account.id == transaction.to_account_id,
                    Account.user_id == current_user.id,
                    Account.is_active == True
                ))
                to_account = to_account.scalars().first()
                if to_account:
                    to_account.balance = (to_account.balance or 0) - transaction.amount

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
    from_account_id: Optional[int] = Query(None, description="Account ID for filtering"),
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
            selectinload(Transaction.from_account),
            selectinload(Transaction.to_account)
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
            # Normalize type to enum (DB uses lowercase enum values)
            t = (transaction_type or "").strip().lower()
            mapping = {
                "income": TransactionType.INCOME,
                "expense": TransactionType.EXPENSE,
                "transfer": TransactionType.TRANSFER,
            }
            if t not in mapping:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid transaction_type. Use income|expense|transfer"
                )
            stmt = stmt.where(Transaction.type == mapping[t])
        if category_id:
            stmt = stmt.where(Transaction.category_id == category_id)
        if sub_category_id:
            stmt = stmt.where(Transaction.sub_category_id == sub_category_id)
        if from_account_id:
            stmt = stmt.where(Transaction.from_account_id == from_account_id)
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
            selectinload(Transaction.from_account),
            selectinload(Transaction.to_account)
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

@router.post("/import", response_model=BaseResponse)
async def import_transactions(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Import transactions from CSV/Excel file."""
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV and Excel files are supported"
            )
        
        # Validate file size (5MB)
        if file.size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 5MB"
            )
        
        # Read file content
        content = await file.read()
        
        # Parse file based on type
        if file.filename.lower().endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        # Validate required columns
        required_columns = ['Date (dd/mm/yy)', 'Account', 'Entry Type', 'Category', 'Sub Category', 'Amount', 'To Account', 'Notes']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Initialize counters
        imported_count = 0
        created_accounts = 0
        created_categories = 0
        created_subcategories = 0
        validation_errors = []
        
        # Note: Transfer transactions no longer use categories/subcategories
        # They are stored as single transactions with from_account_id and to_account_id
        
        # Process each row
        for index, row in df.iterrows():
            try:
                row_num = index + 2  # +2 because index is 0-based and we have header
                
                # Validate entry type
                entry_type = str(row['Entry Type']).lower().strip()
                if entry_type not in ['income', 'expense', 'transfer']:
                    validation_errors.append({
                        'row': row_num,
                        'message': f"Invalid entry type: {entry_type}. Must be 'income', 'expense', or 'transfer'"
                    })
                    continue
                
                # Validate date format
                try:
                    date_str = str(row['Date (dd/mm/yy)']).strip()
                    if pd.isna(date_str) or date_str == '':
                        validation_errors.append({
                            'row': row_num,
                            'message': "Date is required"
                        })
                        continue
                    
                    # Try different date formats
                    date_obj = None
                    for fmt in ['%d/%m/%y', '%d/%m/%Y', '%Y-%m-%d']:
                        try:
                            date_obj = datetime.strptime(date_str, fmt).date()
                            break
                        except ValueError:
                            continue
                    
                    if not date_obj:
                        validation_errors.append({
                            'row': row_num,
                            'message': f"Invalid date format: {date_str}. Expected dd/mm/yy"
                        })
                        continue
                except Exception as e:
                    validation_errors.append({
                        'row': row_num,
                        'message': f"Date parsing error: {str(e)}"
                    })
                    continue
                
                # Validate amount
                try:
                    amount_str = str(row['Amount']).strip()
                    if pd.isna(amount_str) or amount_str == '':
                        validation_errors.append({
                            'row': row_num,
                            'message': "Amount is required"
                        })
                        continue
                    
                    amount = float(amount_str)
                    if amount <= 0:
                        validation_errors.append({
                            'row': row_num,
                            'message': "Amount must be greater than 0"
                        })
                        continue
                except ValueError:
                    validation_errors.append({
                        'row': row_num,
                        'message': f"Invalid amount format: {amount_str}"
                    })
                    continue
                
                # Get or create account
                account_name = str(row['Account']).strip().lower()
                if not account_name:
                    validation_errors.append({
                        'row': row_num,
                        'message': "Account name is required"
                    })
                    continue
                
                account = await db.execute(select(Account).where(
                    and_(Account.name == account_name, Account.user_id == current_user.id, Account.is_active == True)
                ))
                account = account.scalar_one_or_none()
                
                if not account:
                    account = Account(name=account_name, user_id=current_user.id, balance=0.0)
                    db.add(account)
                    await db.flush()
                    created_accounts += 1
                
                # Handle transfer transactions
                if entry_type == 'transfer':
                    # Validate transfer-specific rules
                    category_val = str(row['Category']).strip()
                    subcategory_val = str(row['Sub Category']).strip()
                    to_account_name = str(row['To Account']).strip()
                    
                    if category_val and category_val.lower() != 'nan':
                        validation_errors.append({
                            'row': row_num,
                            'message': "Transfer transactions must have empty category field"
                        })
                        continue
                    
                    if subcategory_val and subcategory_val.lower() != 'nan':
                        validation_errors.append({
                            'row': row_num,
                            'message': "Transfer transactions must have empty subcategory field"
                        })
                        continue
                    
                    if not to_account_name or to_account_name.lower() == 'nan':
                        validation_errors.append({
                            'row': row_num,
                            'message': "Transfer transactions must specify a 'To Account'"
                        })
                        continue
                    
                    # Get or create to_account
                    to_account = await db.execute(select(Account).where(
                        and_(Account.name == to_account_name.lower(), Account.user_id == current_user.id, Account.is_active == True)
                    ))
                    to_account = to_account.scalar_one_or_none()
                    
                    if not to_account:
                        to_account = Account(name=to_account_name.lower(), user_id=current_user.id, balance=0.0)
                        db.add(to_account)
                        await db.flush()
                        created_accounts += 1
                    
                    # Create single transfer transaction
                    transfer_transaction = Transaction(
                        amount=amount,
                        type='transfer',
                        date=date_obj,
                        notes=str(row['Notes']).strip() if pd.notna(row['Notes']) else '',
                        category_id=None,  # Transfers don't have categories
                        sub_category_id=None,  # Transfers don't have sub-categories
                        from_account_id=account.id,
                        to_account_id=to_account.id,
                        user_id=current_user.id
                    )
                    db.add(transfer_transaction)
                    
                    # Update account balances
                    account.balance = (account.balance or 0) - amount
                    to_account.balance = (to_account.balance or 0) + amount
                    
                    imported_count += 1  # Count as 1 transaction
                
                else:
                    # Handle income/expense transactions
                    category_name = str(row['Category']).strip()
                    subcategory_name = str(row['Sub Category']).strip()
                    
                    if not category_name or category_name.lower() == 'nan':
                        validation_errors.append({
                            'row': row_num,
                            'message': f"{entry_type.title()} transactions must have a category"
                        })
                        continue
                    
                    if not subcategory_name or subcategory_name.lower() == 'nan':
                        validation_errors.append({
                            'row': row_num,
                            'message': f"{entry_type.title()} transactions must have a subcategory"
                        })
                        continue
                    
                    # Get or create category
                    category = await db.execute(select(Category).where(
                        and_(Category.name == category_name.lower(), Category.user_id == current_user.id, Category.is_active == True)
                    ))
                    category = category.scalar_one_or_none()
                    
                    if not category:
                        category = Category(name=category_name.lower(), user_id=current_user.id)
                        db.add(category)
                        await db.flush()
                        created_categories += 1
                    
                    # Get or create subcategory
                    subcategory = await db.execute(select(SubCategory).where(
                        and_(SubCategory.name == subcategory_name.lower(), SubCategory.category_id == category.id, SubCategory.user_id == current_user.id, SubCategory.is_active == True)
                    ))
                    subcategory = subcategory.scalar_one_or_none()
                    
                    if not subcategory:
                        subcategory = SubCategory(name=subcategory_name.lower(), category_id=category.id, user_id=current_user.id)
                        db.add(subcategory)
                        await db.flush()
                        created_subcategories += 1
                    
                    # Create transaction
                    transaction = Transaction(
                        amount=amount,
                        type=entry_type,
                        date=date_obj,
                        notes=str(row['Notes']).strip() if pd.notna(row['Notes']) else '',
                        category_id=category.id,
                        sub_category_id=subcategory.id,
                        from_account_id=account.id,
                        user_id=current_user.id
                    )
                    db.add(transaction)
                    
                    # Update account balance
                    if entry_type == 'income':
                        account.balance = (account.balance or 0) + amount
                    else:  # expense
                        account.balance = (account.balance or 0) - amount
                    
                    imported_count += 1
                
            except Exception as e:
                validation_errors.append({
                    'row': row_num if 'row_num' in locals() else index + 2,
                    'message': f"Error processing row: {str(e)}"
                })
                continue
        
        # If there are validation errors, rollback and return errors
        if validation_errors:
            await db.rollback()
            return BaseResponse(
                success=False,
                message="Import failed due to validation errors",
                data={
                    'validationErrors': validation_errors,
                    'importedCount': 0,
                    'createdAccounts': 0,
                    'createdCategories': 0,
                    'createdSubcategories': 0
                }
            )
        
        # Commit all changes
        await db.commit()
        
        return BaseResponse(
            success=True,
            message=f"Successfully imported {imported_count} transactions",
            data={
                'importedCount': imported_count,
                'createdAccounts': created_accounts,
                'createdCategories': created_categories,
                'createdSubcategories': created_subcategories
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )

@router.get("/dashboard-stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics excluding transfer transactions."""
    try:
        # Get total income (excluding transfers)
        income_result = await db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == current_user.id,
                Transaction.is_active == True,
                Transaction.type == TransactionType.INCOME
            )
        )
        total_income = income_result.scalar() or 0.0
        
        # Get total expense (excluding transfers)
        expense_result = await db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == current_user.id,
                Transaction.is_active == True,
                Transaction.type == TransactionType.EXPENSE
            )
        )
        total_expense = expense_result.scalar() or 0.0
        
        # Calculate net balance
        net_balance = total_income - total_expense
        
        # Get transaction count (excluding transfers)
        count_result = await db.execute(
            select(func.count(Transaction.id)).where(
                Transaction.user_id == current_user.id,
                Transaction.is_active == True,
                Transaction.type.in_([TransactionType.INCOME, TransactionType.EXPENSE])
            )
        )
        transaction_count = count_result.scalar() or 0
        
        # Get top categories (excluding transfers)
        top_categories_result = await db.execute(
            select(
                Category.name,
                func.sum(Transaction.amount).label('total_amount'),
                func.count(Transaction.id).label('transaction_count')
            ).join(Transaction).where(
                Transaction.user_id == current_user.id,
                Transaction.is_active == True,
                Transaction.type.in_([TransactionType.INCOME, TransactionType.EXPENSE]),
                Category.is_active == True
            ).group_by(Category.id, Category.name).order_by(
                func.sum(Transaction.amount).desc()
            ).limit(5)
        )
        top_categories = [
            {
                "name": row.name,
                "total_amount": float(row.total_amount),
                "transaction_count": row.transaction_count
            }
            for row in top_categories_result.fetchall()
        ]
        
        # Get recent transactions (excluding transfers)
        recent_transactions_result = await db.execute(
            select(Transaction).options(
                selectinload(Transaction.category),
                selectinload(Transaction.sub_category),
                selectinload(Transaction.from_account),
                selectinload(Transaction.to_account)
            ).where(
                Transaction.user_id == current_user.id,
                Transaction.is_active == True,
                Transaction.type.in_([TransactionType.INCOME, TransactionType.EXPENSE])
            ).order_by(Transaction.date.desc()).limit(10)
        )
        recent_transactions = recent_transactions_result.scalars().all()
        
        return DashboardStats(
            total_income=total_income,
            total_expense=total_expense,
            net_balance=net_balance,
            transaction_count=transaction_count,
            top_categories=top_categories,
            recent_transactions=recent_transactions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard stats: {str(e)}"
        ) 