"""
Review API routes.

Handles creating, reading, updating, and deleting reviews for DJ sets.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.database import get_db
from app.models import Review, User, DJSet, Rating
from app.schemas import ReviewCreate, ReviewUpdate, ReviewResponse, PaginatedResponse
from app.auth import get_current_active_user
from app.core.exceptions import DuplicateEntryError

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a review for a set."""
    # Check if set exists
    result = await db.execute(select(DJSet).where(DJSet.id == review_data.set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Set with ID {review_data.set_id} not found"
        )
    
    # Check if review already exists
    existing = await db.execute(
        select(Review).where(
            Review.user_id == current_user.id,
            Review.set_id == review_data.set_id
        )
    )
    if existing.scalar_one_or_none():
        raise DuplicateEntryError("Review already exists for this set")
    
    # Create review
    new_review = Review(
        user_id=current_user.id,
        set_id=review_data.set_id,
        content=review_data.content,
        contains_spoilers=review_data.contains_spoilers,
        is_public=review_data.is_public
    )
    
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    
    # Load user relationship for response
    await db.refresh(new_review, ["user"])
    
    # Get the user's rating for this set
    rating_result = await db.execute(
        select(Rating).where(
            Rating.user_id == current_user.id,
            Rating.set_id == review_data.set_id
        )
    )
    rating = rating_result.scalar_one_or_none()
    
    # Convert to response schema
    review_dict = ReviewResponse.model_validate(new_review).model_dump()
    review_dict['user_rating'] = rating.rating if rating else None
    return ReviewResponse(**review_dict)


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a single review by ID."""
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID {review_id} not found"
        )
    
    # Load user relationship
    await db.refresh(review, ["user"])
    
    # Get the user's rating for this set
    rating_result = await db.execute(
        select(Rating).where(
            Rating.user_id == review.user_id,
            Rating.set_id == review.set_id
        )
    )
    rating = rating_result.scalar_one_or_none()
    
    # Convert to response schema
    review_dict = ReviewResponse.model_validate(review).model_dump()
    review_dict['user_rating'] = rating.rating if rating else None
    return ReviewResponse(**review_dict)


@router.get("/sets/{set_id}", response_model=PaginatedResponse)
async def get_set_reviews(
    set_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get all reviews for a set (paginated)."""
    # Check if set exists
    result = await db.execute(select(DJSet).where(DJSet.id == set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Set with ID {set_id} not found"
        )
    
    # Build query - only public reviews
    query = select(Review).where(
        Review.set_id == set_id,
        Review.is_public == True
    ).order_by(Review.created_at.desc())
    
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
    
    # Load user relationships and fetch ratings for each review
    review_responses = []
    for review in reviews:
        await db.refresh(review, ["user"])
        
        # Get the user's rating for this set
        rating_result = await db.execute(
            select(Rating).where(
                Rating.user_id == review.user_id,
                Rating.set_id == set_id
            )
        )
        rating = rating_result.scalar_one_or_none()
        
        # Convert to response schema
        review_dict = ReviewResponse.model_validate(review).model_dump()
        review_dict['user_rating'] = rating.rating if rating else None
        review_responses.append(ReviewResponse(**review_dict))
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    return PaginatedResponse(
        items=review_responses,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: UUID,
    review_update: ReviewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a review (only if it belongs to the current user)."""
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID {review_id} not found"
        )
    
    # Check ownership
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this review"
        )
    
    # Update fields
    if review_update.content is not None:
        review.content = review_update.content
    if review_update.contains_spoilers is not None:
        review.contains_spoilers = review_update.contains_spoilers
    if review_update.is_public is not None:
        review.is_public = review_update.is_public
    
    await db.commit()
    await db.refresh(review)
    await db.refresh(review, ["user"])
    
    # Get the user's rating for this set
    rating_result = await db.execute(
        select(Rating).where(
            Rating.user_id == review.user_id,
            Rating.set_id == review.set_id
        )
    )
    rating = rating_result.scalar_one_or_none()
    
    # Convert to response schema
    review_dict = ReviewResponse.model_validate(review).model_dump()
    review_dict['user_rating'] = rating.rating if rating else None
    return ReviewResponse(**review_dict)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a review (only if it belongs to the current user)."""
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID {review_id} not found"
        )
    
    # Check ownership
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this review"
        )
    
    await db.delete(review)
    await db.commit()
    
    return None

