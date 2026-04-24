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
from app.config import settings
import app.services.ra as ra_service
import app.services.ticketmaster as tm_service
import app.services.skiddle as skiddle_service

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


# ============================================================================
# EVENT DISCOVERY — SEARCH (no auth required)
# ============================================================================

@router.get("/search/ra", response_model=dict)
async def search_ra_events(
    keyword: Optional[str] = Query(None),
    location: str = Query(..., description="City name, e.g. 'Berlin'"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
):
    """Search Resident Advisor for electronic music events."""
    try:
        return await ra_service.search_events(
            location=location,
            keyword=keyword,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RA API error: {str(e)}")


@router.get("/search/ticketmaster", response_model=dict)
async def search_ticketmaster_events(
    keyword: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None),
    page: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
):
    """Search Ticketmaster for music events."""
    if not settings.TICKETMASTER_API_KEY:
        raise HTTPException(status_code=503, detail="Ticketmaster API key not configured")
    try:
        return await tm_service.search_events(
            api_key=settings.TICKETMASTER_API_KEY,
            keyword=keyword,
            city=city,
            country_code=country_code,
            page=page,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ticketmaster API error: {str(e)}")


@router.get("/search/skiddle", response_model=dict)
async def search_skiddle_events(
    keyword: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    radius: int = Query(10, ge=1, le=100),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    """Search Skiddle for UK/EU club night events."""
    if not settings.SKIDDLE_API_KEY:
        raise HTTPException(status_code=503, detail="Skiddle API key not configured")
    try:
        return await skiddle_service.search_events(
            api_key=settings.SKIDDLE_API_KEY,
            keyword=keyword,
            latitude=lat,
            longitude=lng,
            radius=radius,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Skiddle API error: {str(e)}")


# ============================================================================
# EVENT DISCOVERY — IMPORT (auth required)
# ============================================================================

async def _get_or_create_event(db: AsyncSession, parsed: dict, current_user: User) -> Event:
    """Check for existing external_id, create Event if not found."""
    external_id = parsed.get("external_id")
    if external_id:
        result = await db.execute(select(Event).where(Event.external_id == external_id))
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    new_event = Event(
        title=parsed["title"],
        dj_name=parsed["dj_name"],
        event_name=parsed.get("event_name"),
        event_date=parsed.get("event_date"),
        venue_location=parsed.get("venue_location"),
        description=parsed.get("description"),
        thumbnail_url=parsed.get("thumbnail_url"),
        ticket_url=parsed.get("ticket_url"),
        external_id=external_id,
        created_by_id=current_user.id,
        is_verified=False,
        confirmation_count=0,
    )
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    return new_event


@router.post("/import/ra", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def import_ra_event(
    body: dict = Body(..., example={"ra_id": "123456"}),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Import an event from Resident Advisor by its RA event ID."""
    ra_id = body.get("ra_id")
    if not ra_id:
        raise HTTPException(status_code=422, detail="ra_id is required")

    # Check dedup first
    external_id = f"ra_{ra_id}"
    result = await db.execute(select(Event).where(Event.external_id == external_id))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    # ra_event_id is the event's own numeric ID (differs from the listing ID in ra_id)
    ra_event_id = body.get("ra_event_id") or ra_id

    try:
        parsed = await ra_service.fetch_event(ra_event_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RA API error: {str(e)}")

    if not parsed:
        raise HTTPException(status_code=404, detail=f"RA event {ra_id} not found")

    return await _get_or_create_event(db, parsed, current_user)


@router.post("/import/ticketmaster", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def import_ticketmaster_event(
    body: dict = Body(..., example={"ticketmaster_id": "Z698xZC2Z17..."}),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Import an event from Ticketmaster by its event ID."""
    if not settings.TICKETMASTER_API_KEY:
        raise HTTPException(status_code=503, detail="Ticketmaster API key not configured")

    tm_id = body.get("ticketmaster_id")
    if not tm_id:
        raise HTTPException(status_code=422, detail="ticketmaster_id is required")

    external_id = f"tm_{tm_id}"
    result = await db.execute(select(Event).where(Event.external_id == external_id))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    try:
        parsed = await tm_service.fetch_event(settings.TICKETMASTER_API_KEY, str(tm_id))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ticketmaster API error: {str(e)}")

    return await _get_or_create_event(db, parsed, current_user)


@router.post("/import/skiddle", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def import_skiddle_event(
    body: dict = Body(..., example={"skiddle_id": "13519767"}),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Import an event from Skiddle by its event ID."""
    if not settings.SKIDDLE_API_KEY:
        raise HTTPException(status_code=503, detail="Skiddle API key not configured")

    skiddle_id = body.get("skiddle_id")
    if not skiddle_id:
        raise HTTPException(status_code=422, detail="skiddle_id is required")

    external_id = f"skiddle_{skiddle_id}"
    result = await db.execute(select(Event).where(Event.external_id == external_id))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    try:
        parsed = await skiddle_service.fetch_event(settings.SKIDDLE_API_KEY, str(skiddle_id))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Skiddle API error: {str(e)}")

    return await _get_or_create_event(db, parsed, current_user)


# ── Attendance ────────────────────────────────────────────────────────────────

@router.get("/{event_id}/attended", response_model=dict)
async def get_attendance(
    event_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Check whether the current user has marked themselves as attended."""
    result = await db.execute(
        select(EventConfirmation).where(
            EventConfirmation.event_id == event_id,
            EventConfirmation.user_id == current_user.id,
        )
    )
    attended = result.scalar_one_or_none() is not None
    return {"attended": attended}


@router.post("/{event_id}/attended", response_model=dict, status_code=status.HTTP_201_CREATED)
async def mark_attended(
    event_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark the current user as having attended this event."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    existing = await db.execute(
        select(EventConfirmation).where(
            EventConfirmation.event_id == event_id,
            EventConfirmation.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        return {"attended": True}

    db.add(EventConfirmation(user_id=current_user.id, event_id=event_id))
    await db.commit()
    return {"attended": True}


@router.delete("/{event_id}/attended", status_code=status.HTTP_204_NO_CONTENT)
async def unmark_attended(
    event_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove the current user's attendance mark for this event."""
    result = await db.execute(
        select(EventConfirmation).where(
            EventConfirmation.event_id == event_id,
            EventConfirmation.user_id == current_user.id,
        )
    )
    confirmation = result.scalar_one_or_none()
    if confirmation:
        await db.delete(confirmation)
        await db.commit()


@router.get("/users/{user_id}/confirmed", response_model=PaginatedResponse)
async def get_user_confirmed_events(
    user_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get all events a user has marked as attended, newest first."""
    query = (
        select(Event)
        .join(EventConfirmation, Event.id == EventConfirmation.event_id)
        .where(EventConfirmation.user_id == user_id)
        .order_by(EventConfirmation.created_at.desc())
    )

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0

    events = (await db.execute(query.offset((page - 1) * limit).limit(limit))).scalars().all()

    from app.schemas import EventResponse
    pages = (total + limit - 1) // limit if total > 0 else 0
    return PaginatedResponse(
        items=[EventResponse.model_validate(e).model_dump() for e in events],
        total=total, page=page, limit=limit, pages=pages
    )
