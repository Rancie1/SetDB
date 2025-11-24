"""
List API routes.

Handles creating, reading, updating, and deleting lists.
Also handles list items (sets in lists).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.database import get_db
from app.models import List, ListItem, User, DJSet
from app.schemas import (
    ListCreate,
    ListUpdate,
    ListResponse,
    ListItemCreate,
    ListItemUpdate,
    ListItemResponse,
    PaginatedResponse
)
from app.auth import get_current_active_user
from app.core.exceptions import DuplicateEntryError

router = APIRouter(prefix="/api/lists", tags=["lists"])


@router.get("", response_model=PaginatedResponse)
async def get_lists(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: UUID = Query(None),
    is_public: bool = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of lists with filtering."""
    # Build query
    query = select(List)
    
    # Apply filters
    if user_id:
        query = query.where(List.user_id == user_id)
    
    if is_public is not None:
        query = query.where(List.is_public == is_public)
    else:
        # Default to only public lists if not authenticated
        query = query.where(List.is_public == True)
    
    query = query.order_by(List.created_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    lists = result.scalars().all()
    
    # Load user relationships
    for list_obj in lists:
        await db.refresh(list_obj, ["user"])
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    return PaginatedResponse(
        items=list(lists),
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.post("", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    list_data: ListCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new list."""
    new_list = List(
        user_id=current_user.id,
        name=list_data.name,
        description=list_data.description,
        is_public=list_data.is_public
    )
    
    db.add(new_list)
    await db.commit()
    await db.refresh(new_list)
    await db.refresh(new_list, ["user"])
    
    return new_list


@router.get("/{list_id}", response_model=ListResponse)
async def get_list(
    list_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a single list by ID with its items."""
    result = await db.execute(select(List).where(List.id == list_id))
    list_obj = result.scalar_one_or_none()
    
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Load relationships
    await db.refresh(list_obj, ["user", "items"])
    
    # Load set information for each item
    for item in list_obj.items:
        await db.refresh(item, ["set"])
    
    return list_obj


@router.put("/{list_id}", response_model=ListResponse)
async def update_list(
    list_id: UUID,
    list_update: ListUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a list (only if user is the owner)."""
    result = await db.execute(select(List).where(List.id == list_id))
    list_obj = result.scalar_one_or_none()
    
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Check ownership
    if list_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this list"
        )
    
    # Update fields
    if list_update.name is not None:
        list_obj.name = list_update.name
    if list_update.description is not None:
        list_obj.description = list_update.description
    if list_update.is_public is not None:
        list_obj.is_public = list_update.is_public
    
    await db.commit()
    await db.refresh(list_obj)
    await db.refresh(list_obj, ["user"])
    
    return list_obj


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a list (only if user is the owner)."""
    result = await db.execute(select(List).where(List.id == list_id))
    list_obj = result.scalar_one_or_none()
    
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    # Check ownership
    if list_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this list"
        )
    
    await db.delete(list_obj)
    await db.commit()
    
    return None


@router.post("/{list_id}/items", response_model=ListItemResponse, status_code=status.HTTP_201_CREATED)
async def add_set_to_list(
    list_id: UUID,
    item_data: ListItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a set to a list."""
    # Check if list exists and user owns it
    result = await db.execute(select(List).where(List.id == list_id))
    list_obj = result.scalar_one_or_none()
    
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    if list_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add items to this list"
        )
    
    # Check if set exists
    set_result = await db.execute(select(DJSet).where(DJSet.id == item_data.set_id))
    set_obj = set_result.scalar_one_or_none()
    
    if not set_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Set with ID {item_data.set_id} not found"
        )
    
    # Check if set already in list
    existing = await db.execute(
        select(ListItem).where(
            ListItem.list_id == list_id,
            ListItem.set_id == item_data.set_id
        )
    )
    if existing.scalar_one_or_none():
        raise DuplicateEntryError("Set already in this list")
    
    # Determine position (append to end if not specified)
    if item_data.position is None:
        max_position_result = await db.execute(
            select(func.max(ListItem.position)).where(ListItem.list_id == list_id)
        )
        max_position = max_position_result.scalar() or 0
        position = max_position + 1
    else:
        position = item_data.position
    
    # Create list item
    new_item = ListItem(
        list_id=list_id,
        set_id=item_data.set_id,
        position=position,
        notes=item_data.notes
    )
    
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    await db.refresh(new_item, ["set"])
    
    return new_item


@router.put("/{list_id}/items/{item_id}", response_model=ListItemResponse)
async def update_list_item(
    list_id: UUID,
    item_id: UUID,
    item_update: ListItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a list item (position or notes)."""
    # Check if list exists and user owns it
    result = await db.execute(select(List).where(List.id == list_id))
    list_obj = result.scalar_one_or_none()
    
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    if list_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update items in this list"
        )
    
    # Check if item exists
    item_result = await db.execute(select(ListItem).where(ListItem.id == item_id))
    item = item_result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List item with ID {item_id} not found"
        )
    
    # Update fields
    if item_update.position is not None:
        item.position = item_update.position
    if item_update.notes is not None:
        item.notes = item_update.notes
    
    await db.commit()
    await db.refresh(item)
    await db.refresh(item, ["set"])
    
    return item


@router.delete("/{list_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_set_from_list(
    list_id: UUID,
    item_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a set from a list."""
    # Check if list exists and user owns it
    result = await db.execute(select(List).where(List.id == list_id))
    list_obj = result.scalar_one_or_none()
    
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List with ID {list_id} not found"
        )
    
    if list_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove items from this list"
        )
    
    # Check if item exists
    item_result = await db.execute(select(ListItem).where(ListItem.id == item_id))
    item = item_result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"List item with ID {item_id} not found"
        )
    
    await db.delete(item)
    await db.commit()
    
    return None

