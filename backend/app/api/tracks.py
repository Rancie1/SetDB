"""
Track tags API routes.

Handles adding, removing, and searching for track tags on sets.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, or_
from uuid import UUID
from typing import Optional, List, Union

from app.database import get_db
from app.models import SetTrack, DJSet, User, TrackConfirmation, TrackRating, Track, TrackSetLink
from sqlalchemy import or_
from sqlalchemy.orm import aliased
from app.schemas import (
    SetTrackCreate,
    SetTrackUpdate,
    SetTrackResponse,
    PaginatedResponse,
    TrackConfirmationCreate,
    TrackConfirmationResponse,
    TrackResponse
)
from app.auth import get_current_active_user
from app.core.exceptions import SetNotFoundError
from app.services import soundcloud_search as soundcloud_search_service
from sqlalchemy import func, case

security = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/api/sets/{set_id}/tracks", tags=["tracks"])

# Separate router for track discovery (without set_id in path)
discover_router = APIRouter(prefix="/api/tracks", tags=["tracks"])


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
    """Get all track tags for a set (both SetTrack and TrackSetLink entries)."""
    # Check if set exists
    result = await db.execute(select(DJSet).where(DJSet.id == set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise SetNotFoundError(str(set_id))
    
    # Get all SetTrack entries for this set with confirmation counts and rating stats
    set_tracks_query = (
        select(
            SetTrack,
            func.sum(case((TrackConfirmation.is_confirmed == True, 1), else_=0)).label('confirmation_count'),
            func.sum(case((TrackConfirmation.is_confirmed == False, 1), else_=0)).label('denial_count'),
            func.avg(TrackRating.rating).label('average_rating'),
            func.count(TrackRating.id).label('rating_count')
        )
        .outerjoin(TrackConfirmation, SetTrack.id == TrackConfirmation.track_id)
        .outerjoin(TrackRating, SetTrack.id == TrackRating.track_id)
        .where(SetTrack.set_id == set_id)
        .group_by(SetTrack.id)
    )
    
    set_tracks_result = await db.execute(set_tracks_query)
    set_tracks_with_stats = set_tracks_result.all()
    
    # Get all TrackSetLink entries for this set
    track_links_query = (
        select(TrackSetLink, Track)
        .join(Track, TrackSetLink.track_id == Track.id)
        .where(TrackSetLink.set_id == set_id)
    )
    
    track_links_result = await db.execute(track_links_query)
    track_links_with_tracks = track_links_result.all()
    
    # Get user's confirmations and ratings if authenticated
    user_confirmations = {}
    user_ratings = {}
    if current_user:
        # Get SetTrack IDs for confirmations
        set_track_ids = [t[0].id for t in set_tracks_with_stats]
        if set_track_ids:
            # Get user confirmations for SetTrack entries
            user_conf_result = await db.execute(
                select(TrackConfirmation)
                .where(
                    TrackConfirmation.user_id == current_user.id,
                    TrackConfirmation.track_id.in_(set_track_ids)
                )
            )
            for conf in user_conf_result.scalars().all():
                if conf.track_id:
                    user_confirmations[conf.track_id] = conf.is_confirmed
        
        # Get Track IDs for ratings (both SetTrack and TrackSetLink reference Track model for ratings)
        track_ids_for_ratings = []
        # From SetTrack entries - we need to check if they have a linked Track
        # Actually, TrackRating references Track.id, not SetTrack.id
        # So we need to get Track IDs from both sources
        for link, track in track_links_with_tracks:
            track_ids_for_ratings.append(track.id)
        
        if track_ids_for_ratings:
            # Get user ratings for linked tracks
            user_rating_result = await db.execute(
                select(TrackRating)
                .where(
                    TrackRating.user_id == current_user.id,
                    TrackRating.track_id.in_(track_ids_for_ratings)
                )
            )
            for rating in user_rating_result.scalars().all():
                user_ratings[rating.track_id] = rating.rating
    
    # Build responses from SetTrack entries
    track_responses = []
    for set_track, conf_count, deny_count, avg_rating, rating_count in set_tracks_with_stats:
        await db.refresh(set_track, ["added_by"])
        track_dict = SetTrackResponse.model_validate(set_track).model_dump()
        if set_track.added_by:
            from app.schemas import UserResponse
            track_dict['added_by'] = UserResponse.model_validate(set_track.added_by).model_dump()
        
        # Add confirmation stats
        track_dict['confirmation_count'] = conf_count or 0
        track_dict['denial_count'] = deny_count or 0
        track_dict['user_confirmation'] = user_confirmations.get(set_track.id)
        track_dict['supports_confirmations'] = True  # SetTrack entries support confirmations
        
        # Add rating stats (SetTrack doesn't have direct Track reference, so no ratings for now)
        track_dict['average_rating'] = float(avg_rating) if avg_rating else None
        track_dict['rating_count'] = rating_count or 0
        track_dict['user_rating'] = None  # SetTrack entries don't have Track ratings
        
        track_responses.append(SetTrackResponse(**track_dict))
    
    # Get TrackSetLink IDs for confirmations
    track_link_ids = [link.id for link, track in track_links_with_tracks]
    link_confirmations = {}
    link_confirmation_counts = {}
    
    if track_link_ids:
        # Get confirmation counts for TrackSetLink entries
        link_conf_query = (
            select(
                TrackConfirmation.track_set_link_id,
                func.sum(case((TrackConfirmation.is_confirmed == True, 1), else_=0)).label('conf_count'),
                func.sum(case((TrackConfirmation.is_confirmed == False, 1), else_=0)).label('deny_count')
            )
            .where(TrackConfirmation.track_set_link_id.in_(track_link_ids))
            .group_by(TrackConfirmation.track_set_link_id)
        )
        link_conf_result = await db.execute(link_conf_query)
        for link_id, conf_count, deny_count in link_conf_result.all():
            link_confirmation_counts[link_id] = {
                'confirmation_count': conf_count or 0,
                'denial_count': deny_count or 0
            }
        
        # Get user confirmations for TrackSetLink entries
        if current_user:
            user_link_conf_result = await db.execute(
                select(TrackConfirmation)
                .where(
                    TrackConfirmation.user_id == current_user.id,
                    TrackConfirmation.track_set_link_id.in_(track_link_ids)
                )
            )
            for conf in user_link_conf_result.scalars().all():
                if conf.track_set_link_id:
                    link_confirmations[conf.track_set_link_id] = conf.is_confirmed
    
    # Build responses from TrackSetLink entries
    for link, track in track_links_with_tracks:
        await db.refresh(link, ["added_by"])
        await db.refresh(track)
        
        # Get rating stats for the Track
        rating_query = (
            select(
                func.avg(TrackRating.rating).label('avg_rating'),
                func.count(TrackRating.id).label('rating_count')
            )
            .where(TrackRating.track_id == track.id)
        )
        rating_result = await db.execute(rating_query)
        rating_row = rating_result.first()
        avg_rating = rating_row[0] if rating_row else None
        rating_count = rating_row[1] or 0
        
        # Get confirmation stats for this link
        link_conf_stats = link_confirmation_counts.get(link.id, {'confirmation_count': 0, 'denial_count': 0})
        
        # Convert TrackSetLink to SetTrackResponse format
        track_dict = {
            'id': link.id,  # Use link ID so it can be identified for deletion
            'set_id': set_id,
            'added_by_id': link.added_by_id,
            'track_name': track.track_name,
            'artist_name': track.artist_name,
            'soundcloud_url': track.soundcloud_url,
            'soundcloud_track_id': track.soundcloud_track_id,
            'position': link.position,
            'timestamp_minutes': float(link.timestamp_minutes) if link.timestamp_minutes is not None else None,
            'created_at': link.created_at,
            'is_top_track': False,  # TrackSetLink entries don't support top tracks
            'top_track_order': None,
            'confirmation_count': link_conf_stats['confirmation_count'],
            'denial_count': link_conf_stats['denial_count'],
            'user_confirmation': link_confirmations.get(link.id),
            'supports_confirmations': True,  # TrackSetLink entries now support confirmations
            'average_rating': float(avg_rating) if avg_rating else None,
            'rating_count': rating_count,
            'user_rating': user_ratings.get(track.id),
        }
        
        if link.added_by:
            from app.schemas import UserResponse
            track_dict['added_by'] = UserResponse.model_validate(link.added_by).model_dump()
        
        track_responses.append(SetTrackResponse(**track_dict))
    
    # Sort all tracks by position and created_at
    track_responses.sort(key=lambda x: (
        x.position if x.position is not None else float('inf'),
        x.created_at
    ))
    
    return track_responses


@router.post("", response_model=SetTrackResponse, status_code=status.HTTP_201_CREATED)
async def add_track_tag(
    set_id: UUID,
    track_data: SetTrackCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a track tag to a set. Can link an existing Track entity or create a new SetTrack."""
    # Check if set exists
    result = await db.execute(select(DJSet).where(DJSet.id == set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise SetNotFoundError(str(set_id))
    
    # If track_id is provided, link existing Track entity via TrackSetLink
    if track_data.track_id:
        # Verify track exists
        track_result = await db.execute(select(Track).where(Track.id == track_data.track_id))
        existing_track = track_result.scalar_one_or_none()
        
        if not existing_track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found"
            )
        
        # Check if link already exists
        existing_link = await db.execute(
            select(TrackSetLink).where(
                TrackSetLink.track_id == track_data.track_id,
                TrackSetLink.set_id == set_id
            )
        )
        if existing_link.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This track is already linked to this set"
            )
        
        # Create TrackSetLink
        new_link = TrackSetLink(
            track_id=track_data.track_id,
            set_id=set_id,
            added_by_id=current_user.id,
            position=track_data.position,
            timestamp_minutes=track_data.timestamp_minutes
        )
        
        db.add(new_link)
        await db.commit()
        await db.refresh(new_link, ["track", "added_by"])
        
        # Convert Track to SetTrackResponse format for consistency
        track = new_link.track
        track_dict = {
            'id': new_link.id,  # Use link ID so it can be identified for deletion
            'set_id': set_id,
            'added_by_id': current_user.id,
            'track_name': track.track_name,
            'artist_name': track.artist_name,
            'soundcloud_url': track.soundcloud_url,
            'soundcloud_track_id': track.soundcloud_track_id,
            'position': new_link.position,
            'timestamp_minutes': float(new_link.timestamp_minutes) if new_link.timestamp_minutes is not None else None,
            'created_at': new_link.created_at,
            'is_top_track': False,
            'top_track_order': None,
        }
        
        if new_link.added_by:
            from app.schemas import UserResponse
            track_dict['added_by'] = UserResponse.model_validate(new_link.added_by).model_dump()
        
        return SetTrackResponse(**track_dict)
    
    # Otherwise, create a new SetTrack (original behavior)
    if not track_data.track_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="track_name is required when track_id is not provided"
        )
    
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
    """Remove a track tag (SetTrack or TrackSetLink) - only if added by current user."""
    # Try to find as SetTrack first
    set_track_result = await db.execute(
        select(SetTrack).where(
            SetTrack.id == track_id,
            SetTrack.set_id == set_id
        )
    )
    set_track = set_track_result.scalar_one_or_none()
    
    if set_track:
        # Check ownership
        if set_track.added_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to remove this track tag"
            )
        
        # Delete related confirmations first (due to foreign key constraint)
        await db.execute(delete(TrackConfirmation).where(TrackConfirmation.track_id == track_id))
        
        # Delete the SetTrack
        await db.execute(delete(SetTrack).where(SetTrack.id == track_id))
        await db.commit()
        return None
    
    # Try to find as TrackSetLink
    link_result = await db.execute(
        select(TrackSetLink).where(
            TrackSetLink.id == track_id,
            TrackSetLink.set_id == set_id
        )
    )
    track_link = link_result.scalar_one_or_none()
    
    if track_link:
        # Check ownership
        if track_link.added_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to remove this track link"
            )
        
        # Delete the TrackSetLink
        await db.execute(delete(TrackSetLink).where(TrackSetLink.id == track_id))
        await db.commit()
        return None
    
    # Not found in either table
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Track tag not found"
    )


@router.post("/{track_id}/confirm", response_model=TrackConfirmationResponse, status_code=status.HTTP_201_CREATED)
async def confirm_track(
    set_id: UUID,
    track_id: UUID,
    confirmation_data: TrackConfirmationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Confirm or deny a track tag. Works for both SetTrack and TrackSetLink entries."""
    # Check if it's a TrackSetLink first
    link_result = await db.execute(
        select(TrackSetLink).where(
            TrackSetLink.id == track_id,
            TrackSetLink.set_id == set_id
        )
    )
    track_link = link_result.scalar_one_or_none()
    
    if track_link:
        # Handle TrackSetLink confirmation
        # Check if user already confirmed/denied this track link
        existing = await db.execute(
            select(TrackConfirmation).where(
                TrackConfirmation.track_set_link_id == track_id,
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
                track_set_link_id=track_id,
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
    
    # Check if track exists and belongs to set (SetTrack)
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
    
    # Handle SetTrack confirmation
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
    """Remove a track confirmation. Works for both SetTrack and TrackSetLink entries."""
    # Try to find confirmation for SetTrack
    result = await db.execute(
        select(TrackConfirmation).where(
            TrackConfirmation.track_id == track_id,
            TrackConfirmation.user_id == current_user.id
        )
    )
    confirmation = result.scalar_one_or_none()
    
    # If not found, try TrackSetLink
    if not confirmation:
        result = await db.execute(
            select(TrackConfirmation).where(
                TrackConfirmation.track_set_link_id == track_id,
                TrackConfirmation.user_id == current_user.id
            )
        )
        confirmation = result.scalar_one_or_none()
    
    if not confirmation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Confirmation not found"
        )
    
    # Delete the confirmation
    await db.execute(delete(TrackConfirmation).where(
        TrackConfirmation.id == confirmation.id
    ))
    await db.commit()
    
    return None


@router.post("/{track_id}/set-top", response_model=SetTrackResponse)
async def set_top_track(
    set_id: UUID,
    track_id: UUID,
    order: int = Query(..., ge=1, le=5, description="Order position (1-5)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a track as a top track and assign it an order (1-5).
    
    If another track already has this order, it will be unmarked as top track.
    """
    # Get the track
    result = await db.execute(
        select(SetTrack).where(
            SetTrack.id == track_id,
            SetTrack.set_id == set_id
        )
    )
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    # Check ownership (only the user who added the track can manage top tracks)
    if track.added_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage top tracks for tracks you added"
        )
    
    # Check if user already has 5 top tracks (excluding current track if it's already a top track)
    existing_top_count = await db.execute(
        select(func.count(SetTrack.id)).where(
            SetTrack.added_by_id == current_user.id,
            SetTrack.is_top_track == True,
            SetTrack.id != track_id
        )
    )
    count = existing_top_count.scalar() or 0
    
    # If this track is not already a top track and user has 5 top tracks, unmark the one with the target order
    if not track.is_top_track and count >= 5:
        existing_order_track = await db.execute(
            select(SetTrack).where(
                SetTrack.added_by_id == current_user.id,
                SetTrack.is_top_track == True,
                SetTrack.top_track_order == order,
                SetTrack.id != track_id
            )
        )
        existing_track = existing_order_track.scalar_one_or_none()
        if existing_track:
            existing_track.is_top_track = False
            existing_track.top_track_order = None
    
    # If another track already has this order (and it's not the current track), unmark it
    existing_order_track = await db.execute(
        select(SetTrack).where(
            SetTrack.added_by_id == current_user.id,
            SetTrack.is_top_track == True,
            SetTrack.top_track_order == order,
            SetTrack.id != track_id
        )
    )
    existing_track = existing_order_track.scalar_one_or_none()
    if existing_track:
        existing_track.is_top_track = False
        existing_track.top_track_order = None
    
    # Mark this track as top track with the specified order
    track.is_top_track = True
    track.top_track_order = order
    
    await db.commit()
    await db.refresh(track, ["added_by"])
    
    # Convert to response schema
    track_dict = SetTrackResponse.model_validate(track).model_dump()
    if track.added_by:
        from app.schemas import UserResponse
        track_dict['added_by'] = UserResponse.model_validate(track.added_by).model_dump()
    
    return SetTrackResponse(**track_dict)


@router.delete("/{track_id}/unset-top", status_code=status.HTTP_204_NO_CONTENT)
async def unset_top_track(
    set_id: UUID,
    track_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a track from top tracks."""
    # Get the track
    result = await db.execute(
        select(SetTrack).where(
            SetTrack.id == track_id,
            SetTrack.set_id == set_id
        )
    )
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    # Check ownership (only the user who added the track can manage top tracks)
    if track.added_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage top tracks for tracks you added"
        )
    
    # Unmark as top track
    track.is_top_track = False
    track.top_track_order = None
    
    await db.commit()
    
    return None


# ============================================================================
# TRACK DISCOVERY ENDPOINTS
# ============================================================================

@discover_router.get("", response_model=PaginatedResponse)
async def discover_tracks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    artist_name: Optional[str] = Query(None),
    sort: str = Query("created_at", pattern="^(created_at|track_name|artist_name|average_rating|rating_count)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Discover and browse independent tracks (not SetTrack).
    
    Query parameters:
    - page: Page number (starts at 1)
    - limit: Items per page (1-100)
    - search: Search in track name and artist name
    - artist_name: Filter by artist name
    - sort: Sort field (created_at, track_name, artist_name, average_rating, rating_count)
    - order: Sort order (asc, desc)
    """
    # Build base query with rating stats - using Track model, not SetTrack
    query = (
        select(
            Track,
            func.avg(TrackRating.rating).label('avg_rating'),
            func.count(TrackRating.id).label('rating_count')
        )
        .outerjoin(TrackRating, Track.id == TrackRating.track_id)
        .group_by(Track.id)
    )
    
    # Apply filters
    if search:
        search_filter = or_(
            Track.track_name.ilike(f"%{search}%"),
            Track.artist_name.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    
    if artist_name:
        query = query.where(Track.artist_name.ilike(f"%{artist_name}%"))
    
    # Apply sorting
    sort_column = None
    if sort == "track_name":
        sort_column = Track.track_name
    elif sort == "artist_name":
        sort_column = Track.artist_name
    elif sort == "average_rating":
        sort_column = func.avg(TrackRating.rating)
    elif sort == "rating_count":
        sort_column = func.count(TrackRating.id)
    else:  # created_at (default)
        sort_column = Track.created_at
    
    if order == "asc":
        query = query.order_by(sort_column.asc().nulls_last())
    else:
        query = query.order_by(sort_column.desc().nulls_last())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    tracks_with_stats = result.all()
    
    # Get user ratings and top track status if authenticated
    user_ratings = {}
    user_top_tracks = {}
    if current_user:
        track_ids = [t[0].id for t in tracks_with_stats]
        if track_ids:
            # Get user ratings
            user_rating_result = await db.execute(
                select(TrackRating)
                .where(
                    TrackRating.user_id == current_user.id,
                    TrackRating.track_id.in_(track_ids)
                )
            )
            for rating in user_rating_result.scalars().all():
                user_ratings[rating.track_id] = rating.rating
            
            # Get user top tracks
            from app.models import UserTopTrack
            user_top_result = await db.execute(
                select(UserTopTrack)
                .where(
                    UserTopTrack.user_id == current_user.id,
                    UserTopTrack.track_id.in_(track_ids)
                )
            )
            for top_track in user_top_result.scalars().all():
                user_top_tracks[top_track.track_id] = {
                    'is_top_track': True,
                    'top_track_order': top_track.order
                }
    
    # Get linked sets count for each track
    from app.models import TrackSetLink
    linked_sets_counts = {}
    if tracks_with_stats:
        track_ids = [t[0].id for t in tracks_with_stats]
        linked_sets_query = (
            select(
                TrackSetLink.track_id,
                func.count(TrackSetLink.id).label('count')
            )
            .where(TrackSetLink.track_id.in_(track_ids))
            .group_by(TrackSetLink.track_id)
        )
        linked_sets_result = await db.execute(linked_sets_query)
        for track_id, count in linked_sets_result.all():
            linked_sets_counts[track_id] = count
    
    # Load relationships and build responses
    track_responses = []
    for track, avg_rating, rating_count in tracks_with_stats:
        track_dict = TrackResponse.model_validate(track).model_dump()
        
        # Add rating stats
        track_dict['average_rating'] = float(avg_rating) if avg_rating else None
        track_dict['rating_count'] = rating_count or 0
        track_dict['user_rating'] = user_ratings.get(track.id)
        track_dict['linked_sets_count'] = linked_sets_counts.get(track.id, 0)
        
        # Add top track status
        top_track_info = user_top_tracks.get(track.id)
        if top_track_info:
            track_dict['is_top_track'] = top_track_info['is_top_track']
            track_dict['top_track_order'] = top_track_info['top_track_order']
        else:
            track_dict['is_top_track'] = False
            track_dict['top_track_order'] = None
        
        track_responses.append(TrackResponse(**track_dict))
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    return PaginatedResponse(
        items=track_responses,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )
