"""
DJ Set API routes.

Handles CRUD operations for DJ sets, search, filtering, and importing
from external sources (YouTube, SoundCloud).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from uuid import UUID, uuid4
from typing import Optional
from datetime import date

from app.database import get_db
from app.models import DJSet, User, SourceType
from app.schemas import (
    DJSetCreate,
    DJSetUpdate,
    DJSetResponse,
    ImportSetRequest,
    PaginatedResponse
)
from app.auth import get_current_active_user
from app.core.exceptions import SetNotFoundError, ForbiddenError, ExternalAPIError
from app.services.set_importer import import_set, import_set_as_live

router = APIRouter(prefix="/api/sets", tags=["sets"])


async def check_duplicate_live_event(
    db: AsyncSession,
    dj_name: str,
    event_date: Optional[date],
    event_name: Optional[str],
    venue_location: Optional[str],
    exclude_set_id: Optional[UUID] = None
) -> Optional[DJSet]:
    """
    Check for duplicate live events based on DJ name, date, event name, and venue.
    
    Returns the duplicate set if found, None otherwise.
    """
    if not event_date:
        return None  # Can't check duplicates without a date
    
    query = select(DJSet).where(
        DJSet.source_type == SourceType.LIVE,
        DJSet.dj_name.ilike(f"%{dj_name}%"),
        DJSet.event_date == event_date
    )
    
    # If we have event name, also match on that
    if event_name:
        query = query.where(DJSet.event_name.ilike(f"%{event_name}%"))
    
    # If we have venue, also match on that
    if venue_location:
        query = query.where(DJSet.venue_location.ilike(f"%{venue_location}%"))
    
    # Exclude current set if updating
    if exclude_set_id:
        query = query.where(DJSet.id != exclude_set_id)
    
    result = await db.execute(query)
    duplicate = result.scalar_one_or_none()
    
    return duplicate


@router.get("", response_model=PaginatedResponse)
async def get_sets(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    dj_name: Optional[str] = Query(None),
    sort: str = Query("created_at", pattern="^(created_at|title|dj_name)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of DJ sets with filtering and search.
    
    Excludes live events - those should be viewed on the events page.
    All sets are shown separately, even if they're linked to the same event.
    
    Query parameters:
    - page: Page number (starts at 1)
    - limit: Items per page (1-100)
    - search: Search in title and DJ name
    - source_type: Filter by source (youtube, soundcloud) - live events are excluded
    - dj_name: Filter by DJ name
    - sort: Sort field (created_at, title, dj_name)
    """
    # Build query - exclude events (they belong on the events page)
    # Include all sets: YouTube, SoundCloud, and live sets
    query = select(DJSet)
    
    # Apply filters
    if search:
        query = query.where(
            or_(
                DJSet.title.ilike(f"%{search}%"),
                DJSet.dj_name.ilike(f"%{search}%")
            )
        )
    
    if source_type:
        try:
            source_enum = SourceType(source_type)
            # Allow filtering by 'live' - this will show live sets (not events)
            query = query.where(DJSet.source_type == source_enum)
            query = query.where(DJSet.source_type == source_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source_type: {source_type}"
            )
    
    if dj_name:
        query = query.where(DJSet.dj_name.ilike(f"%{dj_name}%"))
    
    # Apply sorting
    if sort == "title":
        query = query.order_by(DJSet.title)
    elif sort == "dj_name":
        query = query.order_by(DJSet.dj_name)
    else:  # created_at (default)
        query = query.order_by(DJSet.created_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    sets = result.scalars().all()
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    # Convert SQLAlchemy models to Pydantic schemas
    # Note: Live events are excluded, so no need to add recording_count
    set_responses = [DJSetResponse.model_validate(set_obj) for set_obj in sets]
    
    return PaginatedResponse(
        items=set_responses,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/{set_id}", response_model=DJSetResponse)
async def get_set(
    set_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a single DJ set by ID."""
    result = await db.execute(select(DJSet).where(DJSet.id == set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise SetNotFoundError(str(set_id))
    
    return set_obj


@router.post("", response_model=DJSetResponse, status_code=status.HTTP_201_CREATED)
async def create_set(
    set_data: DJSetCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new DJ set (manual entry).
    
    For live events, checks for duplicates and sets verification status.
    Live events start as unverified and can be confirmed by other users.
    """
    try:
        source_type_enum = SourceType(set_data.source_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source_type: {set_data.source_type}"
        )
    
    # For live sets, they start as unverified
    is_live_set = source_type_enum == SourceType.LIVE
    
    # Validate recording_url - only live sets can have recording URLs
    if set_data.recording_url and source_type_enum != SourceType.LIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="recording_url can only be set for live sets"
        )
    
    # Create new set
    new_set = DJSet(
        title=set_data.title,
        dj_name=set_data.dj_name,
        source_type=source_type_enum,
        source_url=set_data.source_url,
        description=set_data.description,
        thumbnail_url=set_data.thumbnail_url,
        duration_minutes=set_data.duration_minutes,
        event_name=set_data.event_name,
        event_date=set_data.event_date,
        venue_location=set_data.venue_location,
        recording_url=set_data.recording_url,
        created_by_id=current_user.id,
        # Live sets start as unverified
        is_verified=False if is_live_set else True,  # YouTube/SoundCloud are auto-verified
        confirmation_count=0
    )
    
    db.add(new_set)
    await db.commit()
    await db.refresh(new_set)
    
    return new_set


@router.put("/{set_id}", response_model=DJSetResponse)
async def update_set(
    set_id: UUID,
    set_update: DJSetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a DJ set (only if user is the creator)."""
    result = await db.execute(select(DJSet).where(DJSet.id == set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise SetNotFoundError(str(set_id))
    
    # Check if user is the creator
    if set_obj.created_by_id != current_user.id:
        raise ForbiddenError("Only the creator can update this set")
    
    # Update fields
    if set_update.title is not None:
        set_obj.title = set_update.title
    if set_update.dj_name is not None:
        set_obj.dj_name = set_update.dj_name
    if set_update.description is not None:
        set_obj.description = set_update.description
    if set_update.thumbnail_url is not None:
        set_obj.thumbnail_url = set_update.thumbnail_url
    if set_update.duration_minutes is not None:
        set_obj.duration_minutes = set_update.duration_minutes
    if set_update.event_name is not None:
        set_obj.event_name = set_update.event_name
    if set_update.event_date is not None:
        set_obj.event_date = set_update.event_date
    if set_update.venue_location is not None:
        set_obj.venue_location = set_update.venue_location
    if set_update.recording_url is not None:
        # Only allow recording_url for live sets
        if set_update.recording_url and set_obj.source_type != SourceType.LIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="recording_url can only be set for live sets"
            )
        set_obj.recording_url = set_update.recording_url
    
    await db.commit()
    await db.refresh(set_obj)
    
    return set_obj


@router.delete("/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_set(
    set_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a DJ set (only if user is the creator)."""
    result = await db.execute(select(DJSet).where(DJSet.id == set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise SetNotFoundError(str(set_id))
    
    # Check if user is the creator
    if set_obj.created_by_id != current_user.id:
        raise ForbiddenError("Only the creator can delete this set")
    
    # Delete the set
    await db.execute(delete(DJSet).where(DJSet.id == set_id))
    await db.commit()
    
    return None


@router.post("/import/youtube", response_model=DJSetResponse, status_code=status.HTTP_201_CREATED)
async def import_from_youtube(
    import_request: ImportSetRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Import a DJ set from YouTube URL.
    
    Extracts video information from YouTube and creates a DJ set entry.
    If mark_as_live is True, creates a live set with the YouTube URL as recording_url.
    """
    try:
        if import_request.mark_as_live:
            # Import as live set with recording URL
            imported_set = await import_set_as_live(import_request.url, current_user.id, db, source="youtube")
        else:
            # Import as regular YouTube set
            imported_set = await import_set(import_request.url, current_user.id, db, source="youtube")
        # Convert to response schema
        return DJSetResponse.model_validate(imported_set)
    except Exception as e:
        raise ExternalAPIError(f"Failed to import from YouTube: {str(e)}")


@router.post("/import/soundcloud", response_model=DJSetResponse, status_code=status.HTTP_201_CREATED)
async def import_from_soundcloud(
    import_request: ImportSetRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Import a DJ set from SoundCloud URL.
    
    Extracts track information from SoundCloud and creates a DJ set entry.
    If mark_as_live is True, creates a live set with the SoundCloud URL as recording_url.
    """
    try:
        if import_request.mark_as_live:
            # Import as live set with recording URL
            imported_set = await import_set_as_live(import_request.url, current_user.id, db, source="soundcloud")
        else:
            # Import as regular SoundCloud set
            imported_set = await import_set(import_request.url, current_user.id, db, source="soundcloud")
        # Convert to response schema
        return DJSetResponse.model_validate(imported_set)
    except Exception as e:
        raise ExternalAPIError(f"Failed to import from SoundCloud: {str(e)}")


# Event-related endpoints moved to /api/events
# Removed: confirm_event, unconfirm_event, create_live_event_from_set, 
# get_event_linked_sets, link_set_to_event, unlink_set_from_event, search_live_events

@router.post("/{set_id}/mark-as-live", response_model=DJSetResponse)
async def mark_set_as_live(
    set_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Convert an imported set (YouTube/SoundCloud) to a live set.
    
    This converts the set to source_type='live' and stores the original
    source_url as recording_url. The set will appear as a live set on the
    discover page with the recording available.
    """
    # Get the set
    result = await db.execute(select(DJSet).where(DJSet.id == set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise SetNotFoundError(str(set_id))
    
    # Only allow this for YouTube/SoundCloud sets (not already live)
    if set_obj.source_type == SourceType.LIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This set is already a live set"
        )
    
    if set_obj.source_type not in [SourceType.YOUTUBE, SourceType.SOUNDCLOUD]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only YouTube and SoundCloud sets can be marked as live"
        )
    
    # Check if user is the creator
    if set_obj.created_by_id != current_user.id:
        raise ForbiddenError("Only the creator can mark this set as live")
    
    # Store the original source_url as recording_url
    original_source_url = set_obj.source_url
    
    # Generate new source_url for live set
    unique_id = str(uuid4())[:8]
    live_source_url = f"live://{set_obj.dj_name}-{set_obj.title}-{unique_id}"
    
    # Ensure source_url is unique
    max_attempts = 5
    for attempt in range(max_attempts):
        existing_check = await db.execute(
            select(DJSet).where(DJSet.source_url == live_source_url)
        )
        if existing_check.scalar_one_or_none() is None:
            break
        unique_id = str(uuid4())[:8]
        live_source_url = f"live://{set_obj.dj_name}-{set_obj.title}-{unique_id}"
    
    # Convert to live set (NOT an event)
    set_obj.source_type = SourceType.LIVE
    set_obj.source_id = None  # Live sets don't have source_id
    set_obj.source_url = live_source_url
    set_obj.recording_url = original_source_url
    
    await db.commit()
    await db.refresh(set_obj)
    
    return set_obj



