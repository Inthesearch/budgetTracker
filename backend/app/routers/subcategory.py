from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import User, Category, SubCategory, Transaction
from ..schemas import SubCategoryCreate, SubCategoryUpdate, SubCategoryResponse, BaseResponse
from ..auth import get_current_user
from sqlalchemy.future import select

router = APIRouter(prefix="/subcategory", tags=["Sub-Categories"])

@router.post("/addSubCategory", response_model=BaseResponse)
async def add_sub_category(
    sub_category_data: SubCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a new sub-category or link to existing one."""
    # Verify category exists and belongs to user
    result = await db.execute(select(Category).where(
        Category.id == sub_category_data.category_id,
        Category.user_id == current_user.id,
        Category.is_active == True
    ))
    category = result.scalars().first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if sub-category already exists for this user and category
    result = await db.execute(select(SubCategory).where(
        SubCategory.name == sub_category_data.name,
        SubCategory.user_id == current_user.id,
        SubCategory.category_id == sub_category_data.category_id,
        SubCategory.is_active == True
    ))
    existing_sub_category = result.scalars().first()
    
    if existing_sub_category:
        return BaseResponse(
            success=True,
            message="Sub-category already exists",
            data={"sub_category_id": existing_sub_category.id}
        )
    
    # Create new sub-category
    db_sub_category = SubCategory(
        name=sub_category_data.name,
        description=sub_category_data.description,
        user_id=current_user.id,
        category_id=sub_category_data.category_id
    )
    
    db.add(db_sub_category)
    await db.commit()
    await db.refresh(db_sub_category)
    
    return BaseResponse(
        success=True,
        message="Sub-category added successfully",
        data={"sub_category_id": db_sub_category.id}
    )

@router.put("/deleteSubCategory/{sub_category_id}", response_model=BaseResponse)
async def delete_sub_category(
    sub_category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a sub-category."""
    # Find sub-category
    sub_category = await db.execute(select(SubCategory).where(
        SubCategory.id == sub_category_id,
        SubCategory.user_id == current_user.id,
        SubCategory.is_active == True
    ))
    sub_category = sub_category.scalars().first()
    
    if not sub_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sub-category not found"
        )
    
    # Check if sub-category has active transactions
    active_transactions = await db.execute(select(Transaction).where(
        Transaction.sub_category_id == sub_category_id,
        Transaction.is_active == True
    ))
    active_transactions = active_transactions.scalars().first()

    print("active_transactions:" + str(active_transactions))
    
    if active_transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete sub-category with active transactions"
        )
    print("oissue is here")
    # Soft delete sub-category
    sub_category.is_active = False
    await db.commit()
    
    return BaseResponse(
        success=True,
        message="Sub-category deleted successfully"
    )

@router.put("/changeCategory/{sub_category_id}", response_model=BaseResponse)
async def change_sub_category_category(
    sub_category_id: int,
    new_category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change the category of a sub-category."""
    # Find sub-category
    sub_category = await db.execute(select(SubCategory).where(
        SubCategory.id == sub_category_id,
        SubCategory.user_id == current_user.id,
        SubCategory.is_active == True
    ))
    sub_category = sub_category.scalars().first()
    
    if not sub_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sub-category not found"
        )
    
    # Verify new category exists and belongs to user
    new_category = await db.execute(select(Category).where(
        Category.id == new_category_id,
        Category.user_id == current_user.id,
        Category.is_active == True
    ))
    new_category = new_category.scalars().first()
    
    if not new_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="New category not found"
        )
    
    # Check if sub-category name already exists in new category
    existing_sub_category = await db.execute(select(SubCategory).where(
        SubCategory.name == sub_category.name,
        SubCategory.user_id == current_user.id,
        SubCategory.category_id == new_category_id,
        SubCategory.is_active == True,
        SubCategory.id != sub_category_id
    ))
    existing_sub_category = existing_sub_category.scalars().first()
    
    if existing_sub_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sub-category name already exists in the new category"
        )
    
    # Deactivate current sub-category
    sub_category.is_active = False
    
    # Create new sub-category with same name in new category
    new_sub_category = SubCategory(
        name=sub_category.name,
        description=sub_category.description,
        user_id=current_user.id,
        category_id=new_category_id
    )
    
    db.add(new_sub_category)
    await db.commit()
    await db.refresh(new_sub_category)
    
    return BaseResponse(
        success=True,
        message="Sub-category category changed successfully",
        data={"new_sub_category_id": new_sub_category.id}
    )

@router.get("/list/{category_id}", response_model=List[SubCategoryResponse])
async def list_sub_categories(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all active sub-categories for a specific category."""
    # Verify category belongs to user
    category = await db.execute(select(Category).where(
        Category.id == category_id,
        Category.user_id == current_user.id,
        Category.is_active == True
    ))
    category = category.scalars().first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    sub_categories = await db.execute(select(SubCategory).where(
        SubCategory.category_id == category_id,
        SubCategory.user_id == current_user.id,
        SubCategory.is_active == True
    ))
    sub_categories = sub_categories.scalars().all()
    
    return sub_categories 