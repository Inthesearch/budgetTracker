# Case-Insensitive Category and Account System

## Overview

The budget tracker now supports case-insensitive category, subcategory, and account names. This means that "Food", "food", and "FOOD" are all treated as the same category, and "Chase Bank", "chase bank", and "CHASE BANK" are all treated as the same account, preventing duplicates with different capitalization.

## Changes Made

### Backend Changes

1. **Database Models** (`backend/app/models.py`):
   - Added `__init__` methods to `Category`, `SubCategory`, and `Account` models
   - Automatically converts names to lowercase before saving to database

2. **Schemas** (`backend/app/schemas.py`):
   - Added validators to convert category, subcategory, and account names to lowercase
   - Added response formatters to display names in proper case

3. **Routers** (`backend/app/routers/category.py`, `backend/app/routers/subcategory.py`, and `backend/app/routers/account.py`):
   - Updated to perform case-insensitive comparisons when checking for existing categories/subcategories/accounts
   - Ensures new categories/subcategories/accounts are saved in lowercase

4. **Utilities** (`backend/app/utils.py`):
   - Created `to_proper_case()` function for intelligent case formatting
   - Handles common abbreviations (TV, ATM, etc.) and special cases
   - Created `format_category_name()`, `format_subcategory_name()`, and `format_account_name()` functions

### Frontend Changes

1. **Formatters** (`src/utils/formatters.js`):
   - Created JavaScript version of the proper case formatter
   - Handles the same abbreviations and special cases as backend
   - Added `formatAccountName()` function for account name formatting

2. **Components**:
   - Updated `Home.jsx`, `TransactionList.jsx`, and `TransactionModal.jsx`
   - All components now display category, subcategory, and account names in proper case
   - Added proper case formatting for categories, subcategories, and accounts

## How It Works

### Storage
- All category, subcategory, and account names are stored in lowercase in the database
- This ensures consistency and prevents duplicates with different capitalization

### Display
- Names are automatically converted to proper case when displayed
- Common abbreviations (TV, ATM, etc.) remain uppercase
- Special cases like "McDonald" are handled correctly

### Examples

| Input | Stored As | Displayed As |
|-------|-----------|--------------|
| "Food" | "food" | "Food" |
| "FOOD" | "food" | "Food" |
| "fast food" | "fast food" | "Fast Food" |
| "tv shows" | "tv shows" | "TV Shows" |
| "atm withdrawal" | "atm withdrawal" | "ATM Withdrawal" |
| "Chase Bank" | "chase bank" | "Chase Bank" |
| "CHASE BANK" | "chase bank" | "Chase Bank" |
| "wells fargo" | "wells fargo" | "Wells Fargo" |

## Migration

If you have existing data with mixed-case category, subcategory, or account names, run the migration scripts:

```bash
cd backend
# For categories and subcategories
python run_sql_update.py

# For accounts
python run_account_sql_update.py
```

These scripts will convert all existing names to lowercase.

## Benefits

1. **Prevents Duplicates**: Users can't accidentally create "Food" and "food" as separate categories, or "Chase Bank" and "chase bank" as separate accounts
2. **Better UX**: Categories, subcategories, and accounts are displayed in proper case for readability
3. **Consistent Data**: All names are stored consistently in lowercase
4. **Smart Formatting**: Handles abbreviations and special cases intelligently

## Testing

To test the system:

1. Try creating categories with different capitalization (e.g., "Food", "FOOD", "food")
2. Try creating accounts with different capitalization (e.g., "Chase Bank", "CHASE BANK", "chase bank")
3. Verify they all resolve to the same category/account
4. Check that the display shows proper case formatting
5. Test with abbreviations like "TV Shows" or "ATM Withdrawal"
6. Test with bank names like "Wells Fargo" or "Bank of America"
