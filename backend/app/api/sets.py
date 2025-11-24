"""
DJ Set API routes.

Handles CRUD operations for DJ sets, search, filtering, and importing
from external sources (YouTube, SoundCloud).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from uuid import UUID
from typing import Optional

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
from app.services.set_importer import import_set

router = APIRouter(prefix="/api/sets", tags=["sets"])


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
    
    Query parameters:
    - page: Page number (starts at 1)
    - limit: Items per page (1-100)
    - search: Search in title and DJ name
    - source_type: Filter by source (youtube, soundcloud, live)
    - dj_name: Filter by DJ name
    - sort: Sort field (created_at, title, dj_name)
    """
    # Build query
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
    
    return PaginatedResponse(
        items=list(sets),
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
    """Create a new DJ set (manual entry)."""
    try:
        source_type_enum = SourceType(set_data.source_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source_type: {set_data.source_type}"
        )
    
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
        created_by_id=current_user.id
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
    
    await db.delete(set_obj)
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
    """
    try:
        imported_set = await import_set(import_request.url, current_user.id, db, source="youtube")
        return imported_set
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
    """
    try:
        imported_set = await import_set(import_request.url, current_user.id, db, source="soundcloud")
        return imported_set
    except Exception as e:
        raise ExternalAPIError(f"Failed to import from SoundCloud: {str(e)}")

