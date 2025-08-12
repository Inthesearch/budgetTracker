#!/usr/bin/env python3
"""
Script to clean up existing transfer transactions that were stored as separate expense/income entries.
This script will:
1. Find pairs of expense/income transactions with the same amount, date, and notes containing "Transfer"
2. Convert them to single transfer transactions
3. Update account balances accordingly
4. Delete the old expense/income transactions
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import get_db
from app.models import Transaction, Account, TransactionType
from app.config import settings

async def cleanup_transfer_transactions():
    """Clean up existing transfer transactions that were stored as separate expense/income entries."""
    
    # Create async engine - convert sync URL to async URL
    sync_url = settings.database_url
    if sync_url.startswith('postgresql://'):
        async_url = sync_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    else:
        async_url = sync_url
    
    engine = create_async_engine(async_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            print("Starting transfer transaction cleanup...")
            
            # Find all users
            from app.models import User
            users_result = await db.execute(select(User))
            users = users_result.scalars().all()
            
            total_cleaned = 0
            
            for user in users:
                print(f"Processing user: {user.email}")
                
                # Find potential transfer pairs
                # Look for expense transactions with "Transfer" in notes
                expense_transfers = await db.execute(
                    select(Transaction).where(
                        and_(
                            Transaction.user_id == user.id,
                            Transaction.is_active == True,
                            Transaction.type == TransactionType.EXPENSE,
                            Transaction.notes.like('%Transfer%')
                        )
                    )
                )
                expense_transfers = expense_transfers.scalars().all()
                
                print(f"Found {len(expense_transfers)} potential transfer expense transactions")
                
                for expense_tx in expense_transfers:
                    # Look for corresponding income transaction
                    # Same amount, same date, similar notes
                    income_transfers = await db.execute(
                        select(Transaction).where(
                            and_(
                                Transaction.user_id == user.id,
                                Transaction.is_active == True,
                                Transaction.type == TransactionType.INCOME,
                                Transaction.amount == expense_tx.amount,
                                Transaction.date == expense_tx.date,
                                Transaction.notes.like('%Transfer%')
                            )
                        )
                    )
                    income_transfers = income_transfers.scalars().all()
                    
                    if income_transfers:
                        # Found a pair, create a single transfer transaction
                        income_tx = income_transfers[0]  # Take the first match
                        
                        print(f"Found transfer pair: {expense_tx.id} (expense) and {income_tx.id} (income)")
                        
                        # Create new transfer transaction
                        transfer_tx = Transaction(
                            amount=expense_tx.amount,
                            type=TransactionType.TRANSFER,
                            date=expense_tx.date,
                            notes=expense_tx.notes.replace("Transfer to", "").replace("Transfer from", "").strip(),
                            category_id=None,
                            sub_category_id=None,
                            from_account_id=expense_tx.from_account_id,
                            to_account_id=income_tx.from_account_id,
                            user_id=user.id
                        )
                        db.add(transfer_tx)
                        
                        # Deactivate old transactions
                        expense_tx.is_active = False
                        income_tx.is_active = False
                        
                        # Update account balances
                        # The expense transaction already decreased the from_account
                        # The income transaction already increased the to_account
                        # So we don't need to change balances, just ensure they're correct
                        
                        total_cleaned += 1
                        
                        print(f"Created transfer transaction {transfer_tx.id} from {expense_tx.from_account_id} to {income_tx.from_account_id}")
                
                # Commit changes for this user
                await db.commit()
                print(f"Committed changes for user {user.email}")
            
            print(f"Cleanup completed! Total transfer pairs cleaned: {total_cleaned}")
            
        except Exception as e:
            await db.rollback()
            print(f"Error during cleanup: {e}")
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(cleanup_transfer_transactions())
