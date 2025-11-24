"""
User API routes.

Handles user profiles, statistics, and following functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.database import get_db
from app.models import User, Follow, UserSetLog, Review, List, Rating
from app.schemas import UserResponse, UserUpdate, UserStats, PaginatedResponse
from app.auth import get_current_active_user
from app.core.exceptions import ForbiddenError, DuplicateEntryError

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get user profile by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile."""
    # Update only provided fields
    if user_update.display_name is not None:
        current_user.display_name = user_update.display_name
    if user_update.bio is not None:
        current_user.bio = user_update.bio
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.get("/{user_id}/stats", response_model=UserStats)
async def get_user_stats(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics."""
    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Count sets logged
    sets_logged_result = await db.execute(
        select(func.count(UserSetLog.id)).where(UserSetLog.user_id == user_id)
    )
    sets_logged = sets_logged_result.scalar() or 0
    
    # Count reviews written
    reviews_result = await db.execute(
        select(func.count(Review.id)).where(Review.user_id == user_id)
    )
    reviews_written = reviews_result.scalar() or 0
    
    # Count lists created
    lists_result = await db.execute(
        select(func.count(List.id)).where(List.user_id == user_id)
    )
    lists_created = lists_result.scalar() or 0
    
    # Calculate average rating
    avg_rating_result = await db.execute(
        select(func.avg(Rating.rating)).where(Rating.user_id == user_id)
    )
    average_rating = avg_rating_result.scalar()
    
    # Count following
    following_result = await db.execute(
        select(func.count(Follow.id)).where(Follow.follower_id == user_id)
    )
    following_count = following_result.scalar() or 0
    
    # Count followers
    followers_result = await db.execute(
        select(func.count(Follow.id)).where(Follow.following_id == user_id)
    )
    followers_count = followers_result.scalar() or 0
    
    return UserStats(
        sets_logged=sets_logged,
        reviews_written=reviews_written,
        lists_created=lists_created,
        average_rating=float(average_rating) if average_rating else None,
        following_count=following_count,
        followers_count=followers_count
    )


@router.post("/{user_id}/follow", status_code=status.HTTP_201_CREATED)
async def follow_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Follow a user."""
    # Can't follow yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot follow yourself"
        )
    
    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Check if already following
    existing_follow = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id
        )
    )
    if existing_follow.scalar_one_or_none():
        raise DuplicateEntryError("Already following this user")
    
    # Create follow relationship
    follow = Follow(
        follower_id=current_user.id,
        following_id=user_id
    )
    db.add(follow)
    await db.commit()
    
    return {"message": "Successfully followed user"}


@router.delete("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Unfollow a user."""
    # Find follow relationship
    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id
        )
    )
    follow = result.scalar_one_or_none()
    
    if not follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not following this user"
        )
    
    await db.delete(follow)
    await db.commit()
    
    return None


@router.get("/me/feed", response_model=PaginatedResponse)
async def get_user_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity feed from users that the current user follows.
    
    Returns recent activity (reviews, created lists) from followed users.
    Note: In a production app, you'd want a dedicated activity table for better performance.
    """
    # Get list of followed user IDs
    following_result = await db.execute(
        select(Follow.following_id).where(Follow.follower_id == current_user.id)
    )
    following_ids = [row[0] for row in following_result.all()]
    
    if not following_ids:
        return PaginatedResponse(
            items=[],
            total=0,
            page=page,
            limit=limit,
            pages=0
        )
    
    # Get recent reviews from followed users
    recent_reviews = await db.execute(
        select(Review)
        .where(Review.user_id.in_(following_ids), Review.is_public == True)
        .order_by(Review.created_at.desc())
        .limit(limit * 2)
    )
    reviews = recent_reviews.scalars().all()
    
    # Get recent lists from followed users
    recent_lists = await db.execute(
        select(List)
        .where(List.user_id.in_(following_ids), List.is_public == True)
        .order_by(List.created_at.desc())
        .limit(limit * 2)
    )
    lists = recent_lists.scalars().all()
    
    # Combine and sort by date
    items = []
    
    # Add reviews
    for review in reviews:
        await db.refresh(review, ["user", "set"])
        items.append({
            "type": "review",
            "data": review,
            "created_at": review.created_at
        })
    
    # Add lists
    for list_obj in lists:
        await db.refresh(list_obj, ["user"])
        items.append({
            "type": "list",
            "data": list_obj,
            "created_at": list_obj.created_at
        })
    
    # Sort by created_at
    items.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply pagination
    total = len(items)
    offset = (page - 1) * limit
    paginated_items = items[offset:offset + limit]
    
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    return PaginatedResponse(
        items=[item["data"] for item in paginated_items],
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


