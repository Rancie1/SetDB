"""
Event API routes.

Handles CRUD operations for events, search, filtering, and linking sets to events.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from uuid import UUID
from typing import Optional
from datetime import date

from app.database import get_db
from app.models import Event, DJSet, User, EventSet, EventConfirmation
from app.schemas import (
    EventCreate,
    EventUpdate,
    EventResponse,
    CreateLiveEventFromSetRequest,
    PaginatedResponse
)
from app.auth import get_current_active_user
from app.core.exceptions import SetNotFoundError, ForbiddenError, ExternalAPIError

router = APIRouter(prefix="/api/events", tags=["events"])


class EventNotFoundError(HTTPException):
    """Exception raised when an event is not found."""
    def __init__(self, event_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event not found: {event_id}"
        )


@router.get("", response_model=PaginatedResponse)
async def get_events(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    dj_name: Optional[str] = Query(None),
    sort: str = Query("created_at", pattern="^(created_at|title|dj_name|event_date)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of events.
    
    Query parameters:
    - page: Page number (starts at 1)
    - limit: Items per page (1-100)
    - search: Search in title, event name, and venue
    - dj_name: Filter by DJ name
    - sort: Sort field (created_at, title, dj_name, event_date)
    """
    query = select(Event)
    
    # Apply filters
    if search:
        query = query.where(
            or_(
                Event.title.ilike(f"%{search}%"),
                Event.event_name.ilike(f"%{search}%"),
                Event.venue_location.ilike(f"%{search}%")
            )
        )
    
    if dj_name:
        query = query.where(Event.dj_name.ilike(f"%{dj_name}%"))
    
    # Apply sorting
    if sort == "title":
        query = query.order_by(Event.title)
    elif sort == "dj_name":
        query = query.order_by(Event.dj_name)
    elif sort == "event_date":
        query = query.order_by(Event.event_date.desc().nulls_last())
    else:  # created_at (default)
        query = query.order_by(Event.created_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    events = result.scalars().all()
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    # Convert to response schemas
    event_responses = [EventResponse.model_validate(event) for event in events]
    
    return PaginatedResponse(
        items=event_responses,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a single event by ID."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise EventNotFoundError(str(event_id))
    
    return event


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new event."""
    new_event = Event(
        title=event_data.title,
        dj_name=event_data.dj_name,
        event_name=event_data.event_name,
        event_date=event_data.event_date,
        duration_days=event_data.duration_days,
        venue_location=event_data.venue_location,
        description=event_data.description,
        thumbnail_url=event_data.thumbnail_url,
        created_by_id=current_user.id,
        is_verified=False,
        confirmation_count=0
    )
    
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    
    return new_event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    event_update: EventUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an event (only if user is the creator)."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event_obj = result.scalar_one_or_none()
    
    if not event_obj:
        raise EventNotFoundError(str(event_id))
    
    # Check if user is the creator
    if event_obj.created_by_id != current_user.id:
        raise ForbiddenError("Only the creator can update this event")
    
    # Update fields
    if event_update.title is not None:
        event_obj.title = event_update.title
    if event_update.dj_name is not None:
        event_obj.dj_name = event_update.dj_name
    if event_update.event_name is not None:
        event_obj.event_name = event_update.event_name
    if event_update.event_date is not None:
        event_obj.event_date = event_update.event_date
    if event_update.duration_days is not None:
        event_obj.duration_days = event_update.duration_days
    if event_update.venue_location is not None:
        event_obj.venue_location = event_update.venue_location
    if event_update.description is not None:
        event_obj.description = event_update.description
    if event_update.thumbnail_url is not None:
        event_obj.thumbnail_url = event_update.thumbnail_url
    
    await db.commit()
    await db.refresh(event_obj)
    
    return event_obj


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an event (only if user is the creator)."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event_obj = result.scalar_one_or_none()
    
    if not event_obj:
        raise EventNotFoundError(str(event_id))
    
    # Check if user is the creator
    if event_obj.created_by_id != current_user.id:
        raise ForbiddenError("Only the creator can delete this event")
    
    await db.delete(event_obj)
    await db.commit()
    
    return None


@router.get("/{event_id}/linked-sets", response_model=PaginatedResponse)
async def get_event_linked_sets(
    event_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all sets linked to an event.
    
    This returns all sets linked to the specified event via the EventSet table.
    """
    # Check if event exists
    result = await db.execute(select(Event).where(Event.id == event_id))
    event_obj = result.scalar_one_or_none()
    
    if not event_obj:
        raise EventNotFoundError(str(event_id))
    
    # Get all sets linked to this event via EventSet table
    query = select(DJSet).join(
        EventSet, DJSet.id == EventSet.set_id
    ).where(
        EventSet.event_id == event_id
    ).order_by(DJSet.created_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    linked_sets = result.scalars().all()
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    # Convert to response schemas
    from app.schemas import DJSetResponse
    set_responses = [DJSetResponse.model_validate(set_obj) for set_obj in linked_sets]
    
    return PaginatedResponse(
        items=set_responses,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.post("/{event_id}/link-set/{set_id}", response_model=EventResponse)
async def link_set_to_event(
    event_id: UUID,
    set_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Link a set to an event.
    
    This creates a many-to-many relationship between the set and event.
    Sets remain separate and can be linked to multiple events.
    """
    # Get the event
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise EventNotFoundError(str(event_id))
    
    # Get the set to link
    result = await db.execute(select(DJSet).where(DJSet.id == set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise SetNotFoundError(str(set_id))
    
    # Check if already linked
    existing_link = await db.execute(
        select(EventSet).where(
            EventSet.event_id == event_id,
            EventSet.set_id == set_id
        )
    )
    if existing_link.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This set is already linked to this event"
        )
    
    # Create the link via EventSet table
    event_set = EventSet(
        event_id=event_id,
        set_id=set_id
    )
    
    db.add(event_set)
    await db.commit()
    await db.refresh(event)
    
    return event


@router.delete("/{event_id}/link-set/{set_id}", response_model=EventResponse)
async def unlink_set_from_event(
    event_id: UUID,
    set_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Unlink a set from an event.
    """
    # Find and delete the EventSet link
    result = await db.execute(
        select(EventSet).where(
            EventSet.event_id == event_id,
            EventSet.set_id == set_id
        )
    )
    event_set = result.scalar_one_or_none()
    
    if not event_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This set is not linked to this event"
        )
    
    db.delete(event_set)
    await db.commit()
    
    # Return the event
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise EventNotFoundError(str(event_id))
    
    return event


@router.post("/{event_id}/confirm", status_code=status.HTTP_201_CREATED)
async def confirm_event(
    event_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm that you attended a live event.
    
    This helps verify that the event actually happened. After a threshold
    of confirmations (e.g., 3-5 users), the event can be auto-verified.
    """
    # Check if event exists
    result = await db.execute(select(Event).where(Event.id == event_id))
    event_obj = result.scalar_one_or_none()
    
    if not event_obj:
        raise EventNotFoundError(str(event_id))
    
    # Check if user already confirmed
    existing = await db.execute(
        select(EventConfirmation).where(
            EventConfirmation.user_id == current_user.id,
            EventConfirmation.event_id == event_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already confirmed this event"
        )
    
    # Create confirmation
    confirmation = EventConfirmation(
        user_id=current_user.id,
        event_id=event_id
    )
    
    db.add(confirmation)
    
    # Update confirmation count
    event_obj.confirmation_count += 1
    
    # Auto-verify after 3 confirmations
    if event_obj.confirmation_count >= 3:
        event_obj.is_verified = True
    
    await db.commit()
    await db.refresh(event_obj)
    
    return {"message": "Event confirmed", "confirmation_count": event_obj.confirmation_count}


@router.delete("/{event_id}/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def unconfirm_event(
    event_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove your confirmation from an event."""
    # Find confirmation
    result = await db.execute(
        select(EventConfirmation).where(
            EventConfirmation.user_id == current_user.id,
            EventConfirmation.event_id == event_id
        )
    )
    confirmation = result.scalar_one_or_none()
    
    if not confirmation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have not confirmed this event"
        )
    
    # Get event to update count
    result = await db.execute(select(Event).where(Event.id == event_id))
    event_obj = result.scalar_one_or_none()
    
    if not event_obj:
        raise EventNotFoundError(str(event_id))
    
    # Delete confirmation
    db.delete(confirmation)
    
    # Update confirmation count
    event_obj.confirmation_count = max(0, event_obj.confirmation_count - 1)
    
    # Unverify if below threshold
    if event_obj.confirmation_count < 3:
        event_obj.is_verified = False
    
    await db.commit()
    await db.flush()
    
    return None


@router.get("/users/{user_id}/confirmed", response_model=PaginatedResponse)
async def get_user_confirmed_events(
    user_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of events confirmed by a user.
    
    Returns all events that the user has confirmed/attended.
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Build query - get events via EventConfirmation
    query = (
        select(Event)
        .join(EventConfirmation, Event.id == EventConfirmation.event_id)
        .where(EventConfirmation.user_id == user_id)
        .order_by(Event.event_date.desc().nulls_last(), Event.created_at.desc())
    )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    events = result.scalars().all()
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    # Convert to response schemas
    event_responses = [EventResponse.model_validate(event) for event in events]
    
    return PaginatedResponse(
        items=event_responses,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.post("/create-from-set/{set_id}", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event_from_set(
    set_id: UUID,
    event_data: Optional[CreateLiveEventFromSetRequest] = Body(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a live event from an existing YouTube/SoundCloud set.
    
    This creates a new event based on the set's data. The original set
    is NOT automatically linked to the event - users can link sets to events
    manually using the link-set endpoint.
    """
    # Get the original set
    result = await db.execute(select(DJSet).where(DJSet.id == set_id))
    original_set = result.scalar_one_or_none()
    
    if not original_set:
        raise SetNotFoundError(str(set_id))
    
    # Extract event data from the set or use provided data
    event_date = None
    event_name = None
    venue_location = None
    
    if event_data:
        event_date = event_data.event_date
        event_name = event_data.event_name
        venue_location = event_data.venue_location
    elif original_set.extra_metadata and original_set.extra_metadata.get('published_at'):
        # Use published date as event date if available
        try:
            from datetime import datetime
            published_at = original_set.extra_metadata['published_at']
            if isinstance(published_at, str):
                event_date = datetime.fromisoformat(published_at.replace('Z', '+00:00')).date()
        except:
            pass
    
    # Check if an event with matching details already exists
    existing_event = None
    if event_date and original_set.dj_name:
        existing_query = select(Event).where(
            Event.dj_name == original_set.dj_name,
            Event.event_date == event_date
        )
        
        if event_name:
            existing_query = existing_query.where(Event.event_name == event_name)
        else:
            existing_query = existing_query.where(Event.event_name.is_(None))
        
        if venue_location:
            existing_query = existing_query.where(Event.venue_location == venue_location)
        else:
            existing_query = existing_query.where(Event.venue_location.is_(None))
        
        result = await db.execute(existing_query)
        existing_event = result.scalar_one_or_none()
    
    # If an existing event is found, use it; otherwise create a new one
    if existing_event:
        return existing_event
    else:
        # Create new event
        new_event = Event(
            title=original_set.title,
            dj_name=original_set.dj_name,
            event_name=event_name,
            event_date=event_date,
            venue_location=venue_location,
            description=original_set.description,
            thumbnail_url=original_set.thumbnail_url,
            created_by_id=current_user.id,
            is_verified=False,
            confirmation_count=0
        )
        
        db.add(new_event)
        await db.commit()
        await db.refresh(new_event)
        
        return new_event
