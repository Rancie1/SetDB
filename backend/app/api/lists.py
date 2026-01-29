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
from app.models import List, ListItem, User, DJSet, Event, Track, ListType
from app.schemas import (
    ListCreate,
    ListUpdate,
    ListResponse,
    ListItemCreate,
    ListItemUpdate,
    ListItemResponse,
    PaginatedResponse,
    UserResponse,
    DJSetResponse,
    EventResponse,
    TrackResponse
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
    
    # Eager load user and items, then build serializable response (avoid lazy load + ORM in response)
    list_responses = []
    for list_obj in lists:
        await db.refresh(list_obj, ["user", "items"])
        list_type_val = list_obj.list_type.value if hasattr(list_obj.list_type, "value") else str(list_obj.list_type)
        list_responses.append({
            "id": list_obj.id,
            "user_id": list_obj.user_id,
            "name": list_obj.name,
            "description": list_obj.description,
            "list_type": list_type_val,
            "is_public": list_obj.is_public,
            "is_featured": list_obj.is_featured,
            "max_items": list_obj.max_items,
            "created_at": list_obj.created_at,
            "updated_at": list_obj.updated_at,
            "user": UserResponse.model_validate(list_obj.user).model_dump() if list_obj.user else None,
            "items": [],  # Omit items in list index to keep payload small
        })
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    return PaginatedResponse(
        items=list_responses,
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
    # Validate list_type
    try:
        list_type_enum = ListType(list_data.list_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid list_type: {list_data.list_type}. Must be one of: sets, events, venues, tracks"
        )
    
    new_list = List(
        user_id=current_user.id,
        name=list_data.name,
        description=list_data.description,
        list_type=list_type_enum,
        is_public=list_data.is_public,
        max_items=list_data.max_items or 5  # Default to 5 for top 5 lists
    )
    
    db.add(new_list)
    await db.commit()
    await db.refresh(new_list)
    await db.refresh(new_list, ["user", "items"])  # Eager load items (empty) to avoid lazy load in response
    
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
    
    # Load item information based on list type and convert to response format
    items_data = []
    for item in list_obj.items:
        item_dict = ListItemResponse.model_validate(item).model_dump()
        
        if list_obj.list_type == ListType.SETS:
            await db.refresh(item, ["set"])
            if item.set:
                item_dict["set"] = DJSetResponse.model_validate(item.set).model_dump()
        elif list_obj.list_type == ListType.EVENTS:
            await db.refresh(item, ["event"])
            if item.event:
                item_dict["event"] = EventResponse.model_validate(item.event).model_dump()
        elif list_obj.list_type == ListType.TRACKS:
            await db.refresh(item, ["track"])
            if item.track:
                item_dict["track"] = TrackResponse.model_validate(item.track).model_dump()
        # Venues don't need relationship loading (stored as string)
        
        items_data.append(item_dict)
    
    # Convert list to response and add items
    list_dict = ListResponse.model_validate(list_obj).model_dump()
    list_dict["items"] = items_data
    
    return list_dict


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
    if list_update.max_items is not None:
        list_obj.max_items = list_update.max_items
    
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
async def add_item_to_list(
    list_id: UUID,
    item_data: ListItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add an item to a list (polymorphic - supports sets, events, tracks, venues)."""
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
    
    # Check max items limit
    current_count_result = await db.execute(
        select(func.count(ListItem.id)).where(ListItem.list_id == list_id)
    )
    current_count = current_count_result.scalar() or 0
    max_items = list_obj.max_items or 5
    
    if current_count >= max_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"List already has {current_count} items (maximum: {max_items})"
        )
    
    # Validate item type matches list type and item exists
    item_id = None
    item_type = None
    
    if list_obj.list_type == ListType.SETS:
        if not item_data.set_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="set_id is required for sets lists"
            )
        set_result = await db.execute(select(DJSet).where(DJSet.id == item_data.set_id))
        if not set_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Set with ID {item_data.set_id} not found"
            )
        item_id = item_data.set_id
        item_type = "set"
        # Check if already in list
        existing = await db.execute(
            select(ListItem).where(
                ListItem.list_id == list_id,
                ListItem.set_id == item_data.set_id
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateEntryError("Set already in this list")
    
    elif list_obj.list_type == ListType.EVENTS:
        if not item_data.event_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="event_id is required for events lists"
            )
        event_result = await db.execute(select(Event).where(Event.id == item_data.event_id))
        if not event_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {item_data.event_id} not found"
            )
        item_id = item_data.event_id
        item_type = "event"
        # Check if already in list
        existing = await db.execute(
            select(ListItem).where(
                ListItem.list_id == list_id,
                ListItem.event_id == item_data.event_id
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateEntryError("Event already in this list")
    
    elif list_obj.list_type == ListType.TRACKS:
        if not item_data.track_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="track_id is required for tracks lists"
            )
        track_result = await db.execute(select(Track).where(Track.id == item_data.track_id))
        if not track_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Track with ID {item_data.track_id} not found"
            )
        item_id = item_data.track_id
        item_type = "track"
        # Check if already in list
        existing = await db.execute(
            select(ListItem).where(
                ListItem.list_id == list_id,
                ListItem.track_id == item_data.track_id
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateEntryError("Track already in this list")
    
    elif list_obj.list_type == ListType.VENUES:
        if not item_data.venue_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="venue_name is required for venues lists"
            )
        item_id = item_data.venue_name
        item_type = "venue"
        # Check if already in list
        existing = await db.execute(
            select(ListItem).where(
                ListItem.list_id == list_id,
                ListItem.venue_name == item_data.venue_name
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateEntryError("Venue already in this list")
    
    # Determine position (append to end if not specified)
    if item_data.position is None:
        max_position_result = await db.execute(
            select(func.max(ListItem.position)).where(ListItem.list_id == list_id)
        )
        max_position = max_position_result.scalar() or 0
        position = max_position + 1
    else:
        position = item_data.position
    
    # Create list item based on type
    new_item = ListItem(
        list_id=list_id,
        set_id=item_data.set_id if list_obj.list_type == ListType.SETS else None,
        event_id=item_data.event_id if list_obj.list_type == ListType.EVENTS else None,
        track_id=item_data.track_id if list_obj.list_type == ListType.TRACKS else None,
        venue_name=item_data.venue_name if list_obj.list_type == ListType.VENUES else None,
        position=position,
        notes=item_data.notes
    )
    
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    
    # Load appropriate relationship based on type and convert to response
    item_dict = ListItemResponse.model_validate(new_item).model_dump()
    
    if list_obj.list_type == ListType.SETS:
        await db.refresh(new_item, ["set"])
        if new_item.set:
            item_dict["set"] = DJSetResponse.model_validate(new_item.set).model_dump()
    elif list_obj.list_type == ListType.EVENTS:
        await db.refresh(new_item, ["event"])
        if new_item.event:
            item_dict["event"] = EventResponse.model_validate(new_item.event).model_dump()
    elif list_obj.list_type == ListType.TRACKS:
        await db.refresh(new_item, ["track"])
        if new_item.track:
            item_dict["track"] = TrackResponse.model_validate(new_item.track).model_dump()
    
    return item_dict


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
    
    # Load appropriate relationship based on list type and convert to response
    await db.refresh(list_obj, ["list_type"])
    item_dict = ListItemResponse.model_validate(item).model_dump()
    
    if list_obj.list_type == ListType.SETS:
        await db.refresh(item, ["set"])
        if item.set:
            item_dict["set"] = DJSetResponse.model_validate(item.set).model_dump()
    elif list_obj.list_type == ListType.EVENTS:
        await db.refresh(item, ["event"])
        if item.event:
            item_dict["event"] = EventResponse.model_validate(item.event).model_dump()
    elif list_obj.list_type == ListType.TRACKS:
        await db.refresh(item, ["track"])
        if item.track:
            item_dict["track"] = TrackResponse.model_validate(item.track).model_dump()
    
    return item_dict


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

