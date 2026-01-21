"""
Standalone Track API routes.

Handles CRUD operations for independent tracks (not tied to specific sets).
Tracks can be searched on SoundCloud, created, and linked to multiple sets.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete
from uuid import UUID
from typing import Optional, List

from app.database import get_db
from app.models import Track, User, TrackSetLink, DJSet, TrackRating, UserTopTrack
from app.schemas import (
    TrackCreate,
    TrackResponse,
    TrackSetLinkCreate,
    TrackSetLinkResponse,
    PaginatedResponse,
    DJSetResponse
)
from app.auth import get_current_active_user
from app.core.exceptions import SetNotFoundError

router = APIRouter(prefix="/api/tracks", tags=["standalone-tracks"])

security = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Optional dependency to get current user if authenticated."""
    if not credentials:
        return None
    try:
        from app.auth import oauth2_scheme
        from jose import JWTError, jwt
        from app.config import settings
        from sqlalchemy import select
        
        # Decode the token
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Extract user_id from token
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            return None
        
        # Fetch user from database
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        
        return user
    except:
        return None


@router.post("", response_model=TrackResponse, status_code=status.HTTP_201_CREATED)
async def create_track(
    track_data: TrackCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new independent track."""
    # Check if track with same SoundCloud URL/ID already exists
    if track_data.soundcloud_url:
        existing = await db.execute(
            select(Track).where(Track.soundcloud_url == track_data.soundcloud_url)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Track with this SoundCloud URL already exists"
            )
    
    if track_data.soundcloud_track_id:
        existing = await db.execute(
            select(Track).where(Track.soundcloud_track_id == track_data.soundcloud_track_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Track with this SoundCloud track ID already exists"
            )
    
    # Check if track with same Spotify URL/ID already exists
    if track_data.spotify_url:
        existing = await db.execute(
            select(Track).where(Track.spotify_url == track_data.spotify_url)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Track with this Spotify URL already exists"
            )
    
    if track_data.spotify_track_id:
        existing = await db.execute(
            select(Track).where(Track.spotify_track_id == track_data.spotify_track_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Track with this Spotify track ID already exists"
            )
    
    # Create track
    new_track = Track(
        track_name=track_data.track_name,
        artist_name=track_data.artist_name,
        soundcloud_url=track_data.soundcloud_url,
        soundcloud_track_id=track_data.soundcloud_track_id,
        spotify_url=track_data.spotify_url,
        spotify_track_id=track_data.spotify_track_id,
        thumbnail_url=track_data.thumbnail_url,
        duration_ms=track_data.duration_ms,
        created_by_id=current_user.id
    )
    
    db.add(new_track)
    await db.commit()
    await db.refresh(new_track)
    
    # Convert to response
    track_dict = TrackResponse.model_validate(new_track).model_dump()
    track_dict['average_rating'] = None
    track_dict['rating_count'] = 0
    track_dict['linked_sets_count'] = 0
    track_dict['is_top_track'] = False
    track_dict['top_track_order'] = None
    
    return TrackResponse(**track_dict)


@router.get("/{track_id}", response_model=TrackResponse)
async def get_track(
    track_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get a track by ID."""
    result = await db.execute(select(Track).where(Track.id == track_id))
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    # Get rating stats
    rating_query = (
        select(
            func.avg(TrackRating.rating).label('avg_rating'),
            func.count(TrackRating.id).label('rating_count')
        )
        .where(TrackRating.track_id == track_id)
    )
    rating_result = await db.execute(rating_query)
    rating_row = rating_result.first()
    avg_rating = rating_row[0] if rating_row else None
    rating_count = rating_row[1] if rating_row else 0
    
    # Get user's rating if authenticated
    user_rating = None
    if current_user:
        user_rating_result = await db.execute(
            select(TrackRating).where(
                TrackRating.track_id == track_id,
                TrackRating.user_id == current_user.id
            )
        )
        user_rating_obj = user_rating_result.scalar_one_or_none()
        if user_rating_obj:
            user_rating = user_rating_obj.rating
    
    # Get linked sets count
    sets_count_result = await db.execute(
        select(func.count(TrackSetLink.id)).where(TrackSetLink.track_id == track_id)
    )
    linked_sets_count = sets_count_result.scalar() or 0
    
    # Get user's top track status if authenticated
    is_top_track = False
    top_track_order = None
    if current_user:
        top_track_result = await db.execute(
            select(UserTopTrack).where(
                UserTopTrack.track_id == track_id,
                UserTopTrack.user_id == current_user.id
            )
        )
        top_track_obj = top_track_result.scalar_one_or_none()
        if top_track_obj:
            is_top_track = True
            top_track_order = top_track_obj.order
    
    # Convert to response
    track_dict = TrackResponse.model_validate(track).model_dump()
    track_dict['average_rating'] = float(avg_rating) if avg_rating else None
    track_dict['rating_count'] = rating_count
    track_dict['user_rating'] = user_rating
    track_dict['linked_sets_count'] = linked_sets_count
    track_dict['is_top_track'] = is_top_track
    track_dict['top_track_order'] = top_track_order
    
    return TrackResponse(**track_dict)


@router.post("/{track_id}/link-to-set", response_model=TrackSetLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_track_to_set(
    track_id: UUID,
    link_data: TrackSetLinkCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Link a track to a set."""
    # Check if track exists
    track_result = await db.execute(select(Track).where(Track.id == track_id))
    track = track_result.scalar_one_or_none()
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    # Check if set exists
    set_result = await db.execute(select(DJSet).where(DJSet.id == link_data.set_id))
    set_obj = set_result.scalar_one_or_none()
    if not set_obj:
        raise SetNotFoundError(str(link_data.set_id))
    
    # Check if link already exists
    existing = await db.execute(
        select(TrackSetLink).where(
            TrackSetLink.track_id == track_id,
            TrackSetLink.set_id == link_data.set_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Track is already linked to this set"
        )
    
    # Create link
    new_link = TrackSetLink(
        track_id=track_id,
        set_id=link_data.set_id,
        added_by_id=current_user.id,
        position=link_data.position,
        timestamp_minutes=link_data.timestamp_minutes
    )
    
    db.add(new_link)
    await db.commit()
    await db.refresh(new_link, ["track", "set", "added_by"])
    
    # Convert to response
    link_dict = TrackSetLinkResponse.model_validate(new_link).model_dump()
    if new_link.track:
        link_dict['track'] = TrackResponse.model_validate(new_link.track).model_dump()
    if new_link.set:
        link_dict['set'] = DJSetResponse.model_validate(new_link.set).model_dump()
    
    return TrackSetLinkResponse(**link_dict)


@router.delete("/{track_id}/link-to-set/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_track_from_set(
    track_id: UUID,
    set_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Unlink a track from a set."""
    # Check if link exists
    result = await db.execute(
        select(TrackSetLink).where(
            TrackSetLink.track_id == track_id,
            TrackSetLink.set_id == set_id
        )
    )
    link = result.scalar_one_or_none()
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track is not linked to this set"
        )
    
    # Check ownership (only the user who added the link can remove it)
    if link.added_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove this link"
        )
    
    await db.execute(delete(TrackSetLink).where(
        TrackSetLink.track_id == track_id,
        TrackSetLink.set_id == set_id
    ))
    await db.commit()
    
    return None


@router.get("/{track_id}/linked-sets", response_model=List[DJSetResponse])
async def get_track_linked_sets(
    track_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all sets that a track is linked to."""
    # Check if track exists
    track_result = await db.execute(select(Track).where(Track.id == track_id))
    track = track_result.scalar_one_or_none()
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    # Get linked sets
    query = (
        select(DJSet)
        .join(TrackSetLink, TrackSetLink.set_id == DJSet.id)
        .where(TrackSetLink.track_id == track_id)
        .order_by(TrackSetLink.created_at.desc())
    )
    
    result = await db.execute(query)
    sets = result.scalars().all()
    
    return [DJSetResponse.model_validate(s) for s in sets]


@router.post("/{track_id}/set-top", response_model=TrackResponse)
async def set_top_track(
    track_id: UUID,
    order: int = Query(..., ge=1, le=5, description="Order position (1-5)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a track as a top track and assign it an order (1-5)."""
    # Check if track exists
    track_result = await db.execute(select(Track).where(Track.id == track_id))
    track = track_result.scalar_one_or_none()
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    # Check if user already has 5 top tracks (excluding current track)
    existing_top_count = await db.execute(
        select(func.count(UserTopTrack.id)).where(
            UserTopTrack.user_id == current_user.id,
            UserTopTrack.track_id != track_id
        )
    )
    count = existing_top_count.scalar() or 0
    
    # If user has 5 top tracks, unmark the one with the target order
    if count >= 5:
        existing_order_track = await db.execute(
            select(UserTopTrack).where(
                UserTopTrack.user_id == current_user.id,
                UserTopTrack.order == order,
                UserTopTrack.track_id != track_id
            )
        )
        existing_top = existing_order_track.scalar_one_or_none()
        if existing_top:
            await db.execute(delete(UserTopTrack).where(UserTopTrack.id == existing_top.id))
    
    # If another track already has this order, unmark it
    existing_order_track = await db.execute(
        select(UserTopTrack).where(
            UserTopTrack.user_id == current_user.id,
            UserTopTrack.order == order,
            UserTopTrack.track_id != track_id
        )
    )
    existing_top = existing_order_track.scalar_one_or_none()
    if existing_top:
        await db.execute(delete(UserTopTrack).where(UserTopTrack.id == existing_top.id))
    
    # Check if this track is already a top track for this user
    existing_top = await db.execute(
        select(UserTopTrack).where(
            UserTopTrack.user_id == current_user.id,
            UserTopTrack.track_id == track_id
        )
    )
    existing = existing_top.scalar_one_or_none()
    
    if existing:
        # Update order
        existing.order = order
    else:
        # Create new top track entry
        new_top_track = UserTopTrack(
            user_id=current_user.id,
            track_id=track_id,
            order=order
        )
        db.add(new_top_track)
    
    await db.commit()
    
    # Return updated track
    return await get_track(track_id, db, current_user)


@router.delete("/{track_id}/unset-top", status_code=status.HTTP_204_NO_CONTENT)
async def unset_top_track(
    track_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a track from top tracks."""
    # Check if top track entry exists
    result = await db.execute(
        select(UserTopTrack).where(
            UserTopTrack.track_id == track_id,
            UserTopTrack.user_id == current_user.id
        )
    )
    top_track = result.scalar_one_or_none()
    
    if not top_track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track is not in your top tracks"
        )
    
    await db.execute(delete(UserTopTrack).where(
        UserTopTrack.track_id == track_id,
        UserTopTrack.user_id == current_user.id
    ))
    await db.commit()
    
    return None
