"""
Venue API routes.

Handles CRUD and search for venues (first-class entities for top 5 ranking).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.models import Venue
from app.schemas import VenueCreate, VenueUpdate, VenueResponse, PaginatedResponse
from app.auth import get_current_active_user
from app.models import User

router = APIRouter(prefix="/api/venues", tags=["venues"])


@router.get("", response_model=PaginatedResponse)
async def get_venues(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of venues.
    Query parameters:
    - page: Page number (starts at 1)
    - limit: Items per page (1-100)
    - search: Search by venue name or location
    """
    query = select(Venue)
    if search:
        query = query.where(
            or_(
                Venue.name.ilike(f"%{search}%"),
                (Venue.location.isnot(None) & Venue.location.ilike(f"%{search}%"))
            )
        )
    query = query.order_by(Venue.name)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    venues = result.scalars().all()
    pages = (total + limit - 1) // limit if total > 0 else 0

    items = [VenueResponse.model_validate(v) for v in venues]
    return PaginatedResponse(items=items, total=total, page=page, limit=limit, pages=pages)


@router.get("/{venue_id}", response_model=VenueResponse)
async def get_venue(
    venue_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a single venue by ID."""
    result = await db.execute(select(Venue).where(Venue.id == venue_id))
    venue = result.scalar_one_or_none()
    if not venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")
    return venue


@router.post("", response_model=VenueResponse, status_code=status.HTTP_201_CREATED)
async def create_venue(
    payload: VenueCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new venue (e.g. before adding to top 5)."""
    venue = Venue(name=payload.name.strip(), location=payload.location.strip() if payload.location else None)
    db.add(venue)
    await db.commit()
    await db.refresh(venue)
    return venue


@router.patch("/{venue_id}", response_model=VenueResponse)
async def update_venue(
    venue_id: UUID,
    payload: VenueUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a venue (name/location)."""
    result = await db.execute(select(Venue).where(Venue.id == venue_id))
    venue = result.scalar_one_or_none()
    if not venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")
    if payload.name is not None:
        venue.name = payload.name.strip()
    if payload.location is not None:
        venue.location = payload.location.strip() if payload.location else None
    await db.commit()
    await db.refresh(venue)
    return venue
