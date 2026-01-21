"""
Track Rating API routes.

Handles creating, updating, and deleting ratings for tracks.
Also provides rating statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.database import get_db
from app.models import TrackRating, User, Track, TrackReview
from app.schemas import TrackRatingCreate, TrackRatingUpdate, TrackRatingResponse
from app.auth import get_current_active_user
from app.core.exceptions import SetNotFoundError

router = APIRouter(prefix="/api/tracks", tags=["track-ratings"])


@router.post("/{track_id}/ratings", response_model=TrackRatingResponse, status_code=status.HTTP_201_CREATED)
async def create_track_rating(
    track_id: UUID,
    rating_data: TrackRatingCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Rate a track."""
    # Check if track exists
    result = await db.execute(select(Track).where(Track.id == track_id))
    track_obj = result.scalar_one_or_none()
    
    if not track_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track with ID {track_id} not found"
        )
    
    # Verify track_id matches
    if rating_data.track_id != track_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Track ID in URL does not match track ID in request body"
        )
    
    # Check if rating already exists
    existing = await db.execute(
        select(TrackRating).where(
            TrackRating.user_id == current_user.id,
            TrackRating.track_id == track_id
        )
    )
    existing_rating = existing.scalar_one_or_none()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_data.rating
        await db.commit()
        await db.refresh(existing_rating)
        await db.refresh(existing_rating, ["user"])
        return existing_rating
    
    # Create new rating
    new_rating = TrackRating(
        user_id=current_user.id,
        track_id=track_id,
        rating=rating_data.rating
    )
    
    db.add(new_rating)
    await db.commit()
    await db.refresh(new_rating)
    await db.refresh(new_rating, ["user"])
    
    return new_rating


@router.put("/{track_id}/ratings/{rating_id}", response_model=TrackRatingResponse)
async def update_track_rating(
    track_id: UUID,
    rating_id: UUID,
    rating_update: TrackRatingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a track rating."""
    result = await db.execute(
        select(TrackRating).where(
            TrackRating.id == rating_id,
            TrackRating.track_id == track_id
        )
    )
    rating_obj = result.scalar_one_or_none()
    
    if not rating_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )
    
    # Check ownership
    if rating_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this rating"
        )
    
    # Update rating
    rating_obj.rating = rating_update.rating
    await db.commit()
    await db.refresh(rating_obj)
    await db.refresh(rating_obj, ["user"])
    
    return rating_obj


@router.delete("/{track_id}/ratings/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_track_rating(
    track_id: UUID,
    rating_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a track rating."""
    result = await db.execute(
        select(TrackRating).where(
            TrackRating.id == rating_id,
            TrackRating.track_id == track_id
        )
    )
    rating_obj = result.scalar_one_or_none()
    
    if not rating_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )
    
    # Check ownership
    if rating_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this rating"
        )
    
    from sqlalchemy import delete
    await db.execute(delete(TrackRating).where(TrackRating.id == rating_id))
    await db.commit()
    
    return None


@router.get("/{track_id}/ratings/stats")
async def get_track_rating_stats(
    track_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get rating statistics for a track."""
    # Check if track exists
    result = await db.execute(select(Track).where(Track.id == track_id))
    track_obj = result.scalar_one_or_none()
    
    if not track_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track with ID {track_id} not found"
        )
    
    # Calculate average rating
    avg_result = await db.execute(
        select(func.avg(TrackRating.rating)).where(TrackRating.track_id == track_id)
    )
    average_rating = avg_result.scalar()
    
    # Count total ratings
    count_result = await db.execute(
        select(func.count(TrackRating.id)).where(TrackRating.track_id == track_id)
    )
    total_ratings = count_result.scalar() or 0
    
    # Count ratings by value (for distribution)
    distribution = {}
    for rating_value in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]:
        count_result = await db.execute(
            select(func.count(TrackRating.id)).where(
                TrackRating.track_id == track_id,
                TrackRating.rating == rating_value
            )
        )
        distribution[str(rating_value)] = count_result.scalar() or 0
    
    return {
        "track_id": track_id,
        "average_rating": float(average_rating) if average_rating else None,
        "total_ratings": total_ratings,
        "distribution": distribution
    }
