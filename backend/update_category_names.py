#!/usr/bin/env python3
"""
Script to convert existing category and subcategory names to lowercase.
This should be run once after deploying the new case-insensitive system.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import Category, SubCategory
from sqlalchemy import select

async def update_category_names():
    """Convert all category and subcategory names to lowercase."""
    async for db in get_db():
        try:
            # Update category names
            categories = await db.execute(select(Category))
            category_list = categories.scalars().all()
            
            for category in category_list:
                if category.name and category.name != category.name.lower():
                    print(f"Converting category '{category.name}' to '{category.name.lower()}'")
                    category.name = category.name.lower()
            
            # Update subcategory names
            subcategories = await db.execute(select(SubCategory))
            subcategory_list = subcategories.scalars().all()
            
            for subcategory in subcategory_list:
                if subcategory.name and subcategory.name != subcategory.name.lower():
                    print(f"Converting subcategory '{subcategory.name}' to '{subcategory.name.lower()}'")
                    subcategory.name = subcategory.name.lower()
            
            await db.commit()
            print("Successfully updated all category and subcategory names to lowercase.")
            
        except Exception as e:
            print(f"Error updating category names: {e}")
            await db.rollback()
            raise
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(update_category_names())
