from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from typing import List

from ..database import get_db
from ..models import User, Category, Transaction, SubCategory
from ..schemas import CategoryCreate, CategoryUpdate, CategoryResponse, BaseResponse
from ..auth import get_current_user

router = APIRouter(prefix="/category", tags=["Categories"])

@router.post("/addCategory", response_model=BaseResponse)
async def add_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a new category or link to existing one."""
    try:
        # Check if category already exists for this user (case-insensitive)
        stmt = select(Category).where(
            Category.name == category_data.name.lower(),
            Category.user_id == current_user.id,
            Category.is_active == True
        )
        result = await db.execute(stmt)
        existing_category = result.scalar_one_or_none()
        
        if existing_category:
            return BaseResponse(
                success=True,
                message="Category already exists",
                data={"category_id": existing_category.id}
            )
        
        # Create new category
        db_category = Category(
            name=category_data.name,
            description=category_data.description,
            color=category_data.color,
            icon=category_data.icon,
            user_id=current_user.id
        )
        
        db.add(db_category)
        await db.commit()
        await db.refresh(db_category)
        
        return BaseResponse(
            success=True,
            message="Category added successfully",
            data={"category_id": db_category.id}
        )
        
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create category: {str(e)}"
        )

@router.put("/editCategory/{category_id}", response_model=BaseResponse)
async def edit_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Edit an existing category."""
    try:
        # Find category
        stmt = select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id,
            Category.is_active == True
        )
        result = await db.execute(stmt)
        category = result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check if new name conflicts with existing category (case-insensitive)
        if category_data.name and category_data.name.lower() != category.name:
            stmt = select(Category).where(
                Category.name == category_data.name.lower(),
                Category.user_id == current_user.id,
                Category.is_active == True,
                Category.id != category_id
            )
            result = await db.execute(stmt)
            existing_category = result.scalar_one_or_none()
            
            if existing_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category name already exists"
                )
        
        # Update category
        if category_data.name is not None:
            category.name = category_data.name.lower()
        if category_data.description is not None:
            category.description = category_data.description
        if category_data.color is not None:
            category.color = category_data.color
        if category_data.icon is not None:
            category.icon = category_data.icon
        
        await db.commit()
        await db.refresh(category)
        
        return BaseResponse(
            success=True,
            message="Category updated successfully"
        )
        
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update category: {str(e)}"
        )

@router.put("/deleteCategory/{category_id}", response_model=BaseResponse)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a category."""
    try:
        # Find category
        stmt = select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id,
            Category.is_active == True
        )
        result = await db.execute(stmt)
        category = result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check if category has active transactions
        stmt = select(Transaction).where(
            Transaction.category_id == category_id,
            Transaction.is_active == True
        )
        result = await db.execute(stmt)
        active_transactions = len(result.scalars().all())
        
        if active_transactions > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category with active transactions"
            )
        
        # Soft delete category and its sub-categories
        category.is_active = False
        
        # Also deactivate sub-categories
        stmt = select(SubCategory).where(
            SubCategory.category_id == category_id,
            SubCategory.is_active == True
        )
        result = await db.execute(stmt)
        sub_categories = result.scalars().all()
        
        for sub_category in sub_categories:
            sub_category.is_active = False
        
        await db.commit()
        
        return BaseResponse(
            success=True,
            message="Category deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete category: {str(e)}"
        )

@router.get("/list", response_model=List[CategoryResponse])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all active categories for the current user."""
    try:
        stmt = select(Category).where(
            Category.user_id == current_user.id,
            Category.is_active == True
        )
        result = await db.execute(stmt)
        categories = result.scalars().all()
        
        return categories
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve categories: {str(e)}"
        )

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific category by ID."""
    try:
        stmt = select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id,
            Category.is_active == True
        )
        result = await db.execute(stmt)
        category = result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        return category
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve category: {str(e)}"
        ) 