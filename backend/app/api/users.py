"""
User API routes.

Handles user profiles, statistics, and following functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, join, or_
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.models import User, Follow, UserSetLog, Review, List, Rating, DJSet, EventConfirmation, Event, SetTrack, Track, UserTopTrack
from app.schemas import UserResponse, UserUpdate, UserStats, PaginatedResponse, SetTrackResponse, TrackResponse
from app.auth import get_current_active_user
from fastapi import Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config import settings
from app.core.exceptions import ForbiddenError, DuplicateEntryError

router = APIRouter(prefix="/api/users", tags=["users"])

security = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Optional dependency to get current user if authenticated."""
    if not credentials:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            return None
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        return user
    except:
        return None


@router.get("", response_model=PaginatedResponse)
async def search_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for users by username or display name.
    
    Query parameters:
    - page: Page number (starts at 1)
    - limit: Items per page (1-100)
    - search: Search query (searches username and display_name)
    """
    query = select(User)
    
    # Apply search filter
    if search:
        query = query.where(
            or_(
                User.username.ilike(f"%{search}%"),
                User.display_name.ilike(f"%{search}%")
            )
        )
    
    # Order by username
    query = query.order_by(User.username)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    # Convert to response schemas
    user_responses = [UserResponse.model_validate(user) for user in users]
    
    return PaginatedResponse(
        items=user_responses,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/{user_id}/follow-status")
async def get_follow_status(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if current user is following the specified user."""
    if user_id == current_user.id:
        return {"is_following": False, "is_own_profile": True}
    
    result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id
        )
    )
    follow = result.scalar_one_or_none()
    
    return {"is_following": follow is not None, "is_own_profile": False}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user profile by ID.
    
    Optionally authenticated - returns user profile whether authenticated or not.
    """
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
    
    # Calculate total hours listened (from all logged sets, both live and listened)
    # Join UserSetLog with DJSet to get duration_minutes
    hours_result = await db.execute(
        select(func.sum(DJSet.duration_minutes))
        .select_from(UserSetLog)
        .join(DJSet, UserSetLog.set_id == DJSet.id)
        .where(UserSetLog.user_id == user_id)
        .where(DJSet.duration_minutes.isnot(None))
    )
    total_minutes = hours_result.scalar()
    if total_minutes is None:
        total_minutes = 0
    hours_listened = round(total_minutes / 60.0, 1) if total_minutes > 0 else 0.0
    
    # Count distinct venues attended (from events user has confirmed attendance)
    venues_result = await db.execute(
        select(func.count(func.distinct(Event.venue_location)))
        .select_from(EventConfirmation)
        .join(Event, EventConfirmation.event_id == Event.id)
        .where(EventConfirmation.user_id == user_id)
        .where(Event.venue_location.isnot(None))
        .where(Event.venue_location != '')
    )
    venues_attended = venues_result.scalar() or 0
    
    return UserStats(
        sets_logged=sets_logged,
        reviews_written=reviews_written,
        lists_created=lists_created,
        average_rating=float(average_rating) if average_rating else None,
        following_count=following_count,
        followers_count=followers_count,
        hours_listened=hours_listened,
        venues_attended=venues_attended
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


@router.get("/{user_id}/top-tracks", response_model=list)
async def get_user_top_tracks(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a user's top 5 tracks.
    
    Returns the tracks marked as top tracks, ordered by order (1-5).
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Get top tracks ordered by order
    query = (
        select(Track, UserTopTrack.order)
        .join(UserTopTrack, Track.id == UserTopTrack.track_id)
        .where(UserTopTrack.user_id == user_id)
        .order_by(UserTopTrack.order.asc())
        .limit(5)
    )
    
    result = await db.execute(query)
    tracks_with_order = result.all()
    
    # Load relationships and convert to response schemas
    top_tracks = []
    for track, order in tracks_with_order:
        # Get rating stats
        from app.models import TrackRating
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
        rating_count = rating_row[1] if rating_row else 0
        
        track_dict = TrackResponse.model_validate(track).model_dump()
        track_dict['average_rating'] = float(avg_rating) if avg_rating else None
        track_dict['rating_count'] = rating_count
        track_dict['is_top_track'] = True
        track_dict['top_track_order'] = order
        top_tracks.append(track_dict)
    
    return top_tracks


@router.get("/me/friends", response_model=PaginatedResponse)
async def get_my_friends(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of users that the current user is following (friends).
    
    Returns paginated list of friends with their user information.
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
    
    # Get total count
    total = len(following_ids)
    
    # Apply pagination
    offset = (page - 1) * limit
    paginated_ids = following_ids[offset:offset + limit]
    
    # Get user objects
    users_result = await db.execute(
        select(User).where(User.id.in_(paginated_ids))
    )
    users = users_result.scalars().all()
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    # Convert to response schemas
    user_responses = [UserResponse.model_validate(user) for user in users]
    
    return PaginatedResponse(
        items=user_responses,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


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


