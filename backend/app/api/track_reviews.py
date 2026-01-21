"""
Track Review API routes.

Handles creating, reading, updating, and deleting reviews for tracks.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.database import get_db
from app.models import TrackReview, User, Track, TrackRating
from app.schemas import TrackReviewCreate, TrackReviewUpdate, TrackReviewResponse, PaginatedResponse
from app.auth import get_current_active_user
from app.core.exceptions import DuplicateEntryError

router = APIRouter(prefix="/api/tracks", tags=["track-reviews"])


@router.post("/{track_id}/reviews", response_model=TrackReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_track_review(
    track_id: UUID,
    review_data: TrackReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a review for a track."""
    # Check if track exists
    result = await db.execute(select(Track).where(Track.id == track_id))
    track_obj = result.scalar_one_or_none()
    
    if not track_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track with ID {track_id} not found"
        )
    
    # Verify track_id matches
    if review_data.track_id != track_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Track ID in URL does not match track ID in request body"
        )
    
    # Check if review already exists
    existing = await db.execute(
        select(TrackReview).where(
            TrackReview.user_id == current_user.id,
            TrackReview.track_id == track_id
        )
    )
    if existing.scalar_one_or_none():
        raise DuplicateEntryError("Review already exists for this track")
    
    # Create review
    new_review = TrackReview(
        user_id=current_user.id,
        track_id=track_id,
        content=review_data.content,
        contains_spoilers=review_data.contains_spoilers,
        is_public=review_data.is_public
    )
    
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    await db.refresh(new_review, ["user"])
    
    # Get the user's rating for this track
    rating_result = await db.execute(
        select(TrackRating).where(
            TrackRating.user_id == current_user.id,
            TrackRating.track_id == track_id
        )
    )
    user_rating_obj = rating_result.scalar_one_or_none()
    
    # Convert to response schema
    review_dict = TrackReviewResponse.model_validate(new_review).model_dump()
    if user_rating_obj:
        review_dict['user_rating'] = user_rating_obj.rating
    
    return TrackReviewResponse(**review_dict)


@router.get("/{track_id}/reviews", response_model=PaginatedResponse)
async def get_track_reviews(
    track_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get reviews for a track."""
    # Check if track exists
    result = await db.execute(select(Track).where(Track.id == track_id))
    track_obj = result.scalar_one_or_none()
    
    if not track_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track with ID {track_id} not found"
        )
    
    # Build query - only public reviews
    query = (
        select(TrackReview)
        .where(TrackReview.track_id == track_id, TrackReview.is_public == True)
        .order_by(TrackReview.created_at.desc())
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
    reviews = result.scalars().all()
    
    # Load user relationships and get ratings
    review_responses = []
    for review in reviews:
        await db.refresh(review, ["user"])
        
        # Get user's rating for this track
        rating_result = await db.execute(
            select(TrackRating).where(
                TrackRating.user_id == review.user_id,
                TrackRating.track_id == track_id
            )
        )
        user_rating_obj = rating_result.scalar_one_or_none()
        
        review_dict = TrackReviewResponse.model_validate(review).model_dump()
        if user_rating_obj:
            review_dict['user_rating'] = user_rating_obj.rating
        
        review_responses.append(TrackReviewResponse(**review_dict))
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    return PaginatedResponse(
        items=review_responses,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.put("/{track_id}/reviews/{review_id}", response_model=TrackReviewResponse)
async def update_track_review(
    track_id: UUID,
    review_id: UUID,
    review_update: TrackReviewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a track review."""
    result = await db.execute(
        select(TrackReview).where(
            TrackReview.id == review_id,
            TrackReview.track_id == track_id
        )
    )
    review_obj = result.scalar_one_or_none()
    
    if not review_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check ownership
    if review_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this review"
        )
    
    # Update fields
    if review_update.content is not None:
        review_obj.content = review_update.content
    if review_update.contains_spoilers is not None:
        review_obj.contains_spoilers = review_update.contains_spoilers
    if review_update.is_public is not None:
        review_obj.is_public = review_update.is_public
    
    await db.commit()
    await db.refresh(review_obj)
    await db.refresh(review_obj, ["user"])
    
    # Get user's rating
    rating_result = await db.execute(
        select(TrackRating).where(
            TrackRating.user_id == current_user.id,
            TrackRating.track_id == track_id
        )
    )
    user_rating_obj = rating_result.scalar_one_or_none()
    
    review_dict = TrackReviewResponse.model_validate(review_obj).model_dump()
    if user_rating_obj:
        review_dict['user_rating'] = user_rating_obj.rating
    
    return TrackReviewResponse(**review_dict)


@router.delete("/{track_id}/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_track_review(
    track_id: UUID,
    review_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a track review."""
    result = await db.execute(
        select(TrackReview).where(
            TrackReview.id == review_id,
            TrackReview.track_id == track_id
        )
    )
    review_obj = result.scalar_one_or_none()
    
    if not review_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check ownership
    if review_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this review"
        )
    
    from sqlalchemy import delete
    await db.execute(delete(TrackReview).where(TrackReview.id == review_id))
    await db.commit()
    
    return None
