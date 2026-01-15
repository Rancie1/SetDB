"""
Rating API routes.

Handles creating, updating, and deleting ratings for DJ sets.
Also provides rating statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from collections import defaultdict

from app.database import get_db
from app.models import Rating, User, DJSet
from app.schemas import RatingCreate, RatingUpdate, RatingResponse, RatingStats
from app.auth import get_current_active_user
from app.core.exceptions import SetNotFoundError

router = APIRouter(prefix="/api/ratings", tags=["ratings"])


@router.post("", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def create_rating(
    rating_data: RatingCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Rate a set."""
    # Check if set exists
    result = await db.execute(select(DJSet).where(DJSet.id == rating_data.set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise SetNotFoundError(str(rating_data.set_id))
    
    # Check if rating already exists
    existing = await db.execute(
        select(Rating).where(
            Rating.user_id == current_user.id,
            Rating.set_id == rating_data.set_id
        )
    )
    existing_rating = existing.scalar_one_or_none()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_data.rating
        await db.commit()
        await db.refresh(existing_rating)
        return existing_rating
    
    # Create new rating
    new_rating = Rating(
        user_id=current_user.id,
        set_id=rating_data.set_id,
        rating=rating_data.rating
    )
    
    db.add(new_rating)
    await db.commit()
    await db.refresh(new_rating)
    
    return new_rating


@router.put("/{rating_id}", response_model=RatingResponse)
async def update_rating(
    rating_id: UUID,
    rating_update: RatingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a rating (only if it belongs to the current user)."""
    result = await db.execute(select(Rating).where(Rating.id == rating_id))
    rating = result.scalar_one_or_none()
    
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rating with ID {rating_id} not found"
        )
    
    # Check ownership
    if rating.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this rating"
        )
    
    # Update rating
    rating.rating = rating_update.rating
    
    await db.commit()
    await db.refresh(rating)
    
    return rating


@router.delete("/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rating(
    rating_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a rating (only if it belongs to the current user)."""
    result = await db.execute(select(Rating).where(Rating.id == rating_id))
    rating = result.scalar_one_or_none()
    
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rating with ID {rating_id} not found"
        )
    
    # Check ownership
    if rating.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this rating"
        )
    
    await db.delete(rating)
    await db.commit()
    
    return None


@router.get("/sets/{set_id}/my-rating", response_model=RatingResponse)
async def get_my_rating(
    set_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the current user's rating for a set."""
    # Check if set exists
    result = await db.execute(select(DJSet).where(DJSet.id == set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise SetNotFoundError(str(set_id))
    
    # Get user's rating
    rating_result = await db.execute(
        select(Rating).where(
            Rating.set_id == set_id,
            Rating.user_id == current_user.id
        )
    )
    rating = rating_result.scalar_one_or_none()
    
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You haven't rated this set yet"
        )
    
    return rating


@router.get("/sets/{set_id}/stats", response_model=RatingStats)
async def get_set_rating_stats(
    set_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get rating statistics for a set."""
    # Check if set exists
    result = await db.execute(select(DJSet).where(DJSet.id == set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise SetNotFoundError(str(set_id))
    
    # Get all ratings for this set
    ratings_result = await db.execute(
        select(Rating.rating).where(Rating.set_id == set_id)
    )
    ratings = ratings_result.scalars().all()
    
    if not ratings:
        return RatingStats(
            average_rating=None,
            total_ratings=0,
            rating_distribution={}
        )
    
    # Calculate average
    average_rating = sum(ratings) / len(ratings)
    
    # Calculate distribution
    distribution = defaultdict(int)
    for rating in ratings:
        distribution[rating] += 1
    
    return RatingStats(
        average_rating=round(average_rating, 2),
        total_ratings=len(ratings),
        rating_distribution=dict(distribution)
    )

