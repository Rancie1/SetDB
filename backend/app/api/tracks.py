"""
Track tags API routes.

Handles adding, removing, and searching for track tags on sets.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from uuid import UUID
from typing import Optional, List, Union

from app.database import get_db
from app.models import SetTrack, DJSet, User, TrackConfirmation
from app.schemas import (
    SetTrackCreate,
    SetTrackUpdate,
    SetTrackResponse,
    PaginatedResponse,
    TrackConfirmationCreate,
    TrackConfirmationResponse
)
from app.auth import get_current_active_user
from app.core.exceptions import SetNotFoundError
from app.services import soundcloud_search as soundcloud_search_service
from sqlalchemy import func, case

security = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/api/sets/{set_id}/tracks", tags=["tracks"])


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


@router.get("", response_model=List[SetTrackResponse])
async def get_set_tracks(
    set_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get all track tags for a set."""
    # Check if set exists
    result = await db.execute(select(DJSet).where(DJSet.id == set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise SetNotFoundError(str(set_id))
    
    # Get all tracks for this set with confirmation counts
    tracks_query = (
        select(
            SetTrack,
            func.sum(case((TrackConfirmation.is_confirmed == True, 1), else_=0)).label('confirmation_count'),
            func.sum(case((TrackConfirmation.is_confirmed == False, 1), else_=0)).label('denial_count')
        )
        .outerjoin(TrackConfirmation, SetTrack.id == TrackConfirmation.track_id)
        .where(SetTrack.set_id == set_id)
        .group_by(SetTrack.id)
        .order_by(SetTrack.position.asc().nulls_last(), SetTrack.created_at.asc())
    )
    
    result = await db.execute(tracks_query)
    tracks_with_counts = result.all()
    
    # Get user's confirmations if authenticated
    user_confirmations = {}
    if current_user:
        track_ids = [t[0].id for t in tracks_with_counts]
        if track_ids:
            user_conf_result = await db.execute(
                select(TrackConfirmation)
                .where(
                    TrackConfirmation.user_id == current_user.id,
                    TrackConfirmation.track_id.in_(track_ids)
                )
            )
            for conf in user_conf_result.scalars().all():
                user_confirmations[conf.track_id] = conf.is_confirmed
    
    # Load user relationships and build responses
    track_responses = []
    for track, conf_count, deny_count in tracks_with_counts:
        await db.refresh(track, ["added_by"])
        track_dict = SetTrackResponse.model_validate(track).model_dump()
        if track.added_by:
            from app.schemas import UserResponse
            track_dict['added_by'] = UserResponse.model_validate(track.added_by).model_dump()
        
        # Add confirmation stats
        track_dict['confirmation_count'] = conf_count or 0
        track_dict['denial_count'] = deny_count or 0
        track_dict['user_confirmation'] = user_confirmations.get(track.id)
        
        track_responses.append(SetTrackResponse(**track_dict))
    
    return track_responses


@router.post("", response_model=SetTrackResponse, status_code=status.HTTP_201_CREATED)
async def add_track_tag(
    set_id: UUID,
    track_data: SetTrackCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a track tag to a set."""
    # Check if set exists
    result = await db.execute(select(DJSet).where(DJSet.id == set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise SetNotFoundError(str(set_id))
    
    # Check if track already exists (based on unique constraint)
    existing = await db.execute(
        select(SetTrack).where(
            SetTrack.set_id == set_id,
            SetTrack.track_name == track_data.track_name,
            SetTrack.artist_name == track_data.artist_name
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This track is already tagged for this set"
        )
    
    # If SoundCloud URL provided, try to resolve it to get track ID
    soundcloud_track_id = None
    if track_data.soundcloud_url:
        track_info = await soundcloud_search_service.resolve_soundcloud_url(track_data.soundcloud_url)
        if track_info:
            soundcloud_track_id = str(track_info.get("id"))
    
    # Create track tag
    new_track = SetTrack(
        set_id=set_id,
        added_by_id=current_user.id,
        track_name=track_data.track_name,
        artist_name=track_data.artist_name,
        soundcloud_url=track_data.soundcloud_url,
        soundcloud_track_id=soundcloud_track_id,
        position=track_data.position,
        timestamp_minutes=track_data.timestamp_minutes
    )
    
    db.add(new_track)
    await db.commit()
    await db.refresh(new_track, ["added_by"])
    
    # Convert to response
    track_dict = SetTrackResponse.model_validate(new_track).model_dump()
    if new_track.added_by:
        from app.schemas import UserResponse
        track_dict['added_by'] = UserResponse.model_validate(new_track.added_by).model_dump()
    
    return SetTrackResponse(**track_dict)


@router.put("/{track_id}", response_model=SetTrackResponse)
async def update_track_tag(
    set_id: UUID,
    track_id: UUID,
    track_update: SetTrackUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a track tag (only if added by current user)."""
    result = await db.execute(
        select(SetTrack).where(
            SetTrack.id == track_id,
            SetTrack.set_id == set_id
        )
    )
    track_obj = result.scalar_one_or_none()
    
    if not track_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track tag not found"
        )
    
    # Check ownership
    if track_obj.added_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this track tag"
        )
    
    # Update fields
    if track_update.track_name is not None:
        track_obj.track_name = track_update.track_name
    if track_update.artist_name is not None:
        track_obj.artist_name = track_update.artist_name
    if track_update.soundcloud_url is not None:
        track_obj.soundcloud_url = track_update.soundcloud_url
        # Re-resolve SoundCloud URL if changed
        if track_update.soundcloud_url:
            track_info = await soundcloud_search_service.resolve_soundcloud_url(track_update.soundcloud_url)
            if track_info:
                track_obj.soundcloud_track_id = str(track_info.get("id"))
    if track_update.position is not None:
        track_obj.position = track_update.position
    if track_update.timestamp_minutes is not None:
        track_obj.timestamp_minutes = track_update.timestamp_minutes
    
    await db.commit()
    await db.refresh(track_obj, ["added_by"])
    
    # Convert to response
    track_dict = SetTrackResponse.model_validate(track_obj).model_dump()
    if track_obj.added_by:
        from app.schemas import UserResponse
        track_dict['added_by'] = UserResponse.model_validate(track_obj.added_by).model_dump()
    
    return SetTrackResponse(**track_dict)


@router.delete("/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_track_tag(
    set_id: UUID,
    track_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a track tag (only if added by current user)."""
    result = await db.execute(
        select(SetTrack).where(
            SetTrack.id == track_id,
            SetTrack.set_id == set_id
        )
    )
    track_obj = result.scalar_one_or_none()
    
    if not track_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track tag not found"
        )
    
    # Check ownership
    if track_obj.added_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove this track tag"
        )
    
    # Delete related confirmations first (due to foreign key constraint)
    await db.execute(delete(TrackConfirmation).where(TrackConfirmation.track_id == track_id))
    
    # Delete the track
    await db.execute(delete(SetTrack).where(SetTrack.id == track_id))
    await db.commit()
    
    return None


@router.post("/{track_id}/confirm", response_model=TrackConfirmationResponse, status_code=status.HTTP_201_CREATED)
async def confirm_track(
    set_id: UUID,
    track_id: UUID,
    confirmation_data: TrackConfirmationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Confirm or deny a track tag."""
    # Check if track exists and belongs to set
    result = await db.execute(
        select(SetTrack).where(
            SetTrack.id == track_id,
            SetTrack.set_id == set_id
        )
    )
    track_obj = result.scalar_one_or_none()
    
    if not track_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track tag not found"
        )
    
    # Check if user already confirmed/denied this track
    existing = await db.execute(
        select(TrackConfirmation).where(
            TrackConfirmation.track_id == track_id,
            TrackConfirmation.user_id == current_user.id
        )
    )
    existing_conf = existing.scalar_one_or_none()
    
    if existing_conf:
        # Update existing confirmation
        existing_conf.is_confirmed = confirmation_data.is_confirmed
        await db.commit()
        await db.refresh(existing_conf, ["user"])
        
        conf_dict = TrackConfirmationResponse.model_validate(existing_conf).model_dump()
        if existing_conf.user:
            from app.schemas import UserResponse
            conf_dict['user'] = UserResponse.model_validate(existing_conf.user).model_dump()
        return TrackConfirmationResponse(**conf_dict)
    else:
        # Create new confirmation
        new_confirmation = TrackConfirmation(
            track_id=track_id,
            user_id=current_user.id,
            is_confirmed=confirmation_data.is_confirmed
        )
        db.add(new_confirmation)
        await db.commit()
        await db.refresh(new_confirmation, ["user"])
        
        conf_dict = TrackConfirmationResponse.model_validate(new_confirmation).model_dump()
        if new_confirmation.user:
            from app.schemas import UserResponse
            conf_dict['user'] = UserResponse.model_validate(new_confirmation.user).model_dump()
        return TrackConfirmationResponse(**conf_dict)


@router.delete("/{track_id}/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def remove_track_confirmation(
    set_id: UUID,
    track_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a track confirmation."""
    result = await db.execute(
        select(TrackConfirmation).where(
            TrackConfirmation.track_id == track_id,
            TrackConfirmation.user_id == current_user.id
        )
    )
    confirmation = result.scalar_one_or_none()
    
    if not confirmation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Confirmation not found"
        )
    
    await db.execute(delete(TrackConfirmation).where(
        TrackConfirmation.track_id == track_id,
        TrackConfirmation.user_id == current_user.id
    ))
    await db.commit()
    
    return None
