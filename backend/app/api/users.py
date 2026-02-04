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
from app.models import User, Follow, UserSetLog, Review, List, Rating, DJSet, EventConfirmation, Event, SetTrack, Track, UserTopTrack, UserTopEvent, UserTopVenue, Venue, TrackReview, TrackRating
from app.schemas import UserResponse, UserUpdate, UserStats, PaginatedResponse, SetTrackResponse, TrackResponse, ActivityItem, ReviewResponse, RatingResponse, TrackReviewResponse, TrackRatingResponse, DJSetResponse, LogResponse, EventResponse, VenueResponse
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


@router.get("/activity-feed")
async def get_activity_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    friends_only: str = Query("false"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get activity feed showing reviews, ratings, top track/set additions, and event activities.
    
    Returns activity from:
    - Set reviews and ratings
    - Track reviews and ratings  
    - Top track additions (when users add tracks to their top 5)
    - Top set additions (when users add sets to their top 5)
    - Event creation (when users create events)
    - Event confirmations (when users confirm they attended events)
    
    If friends_only='true' and user is authenticated, only shows activity from followed users.
    If friends_only='false' or omitted or user is not authenticated, shows all public activity.
    """
    # Convert string to boolean - handle various boolean representations
    friends_only_lower = str(friends_only).lower().strip() if friends_only else "false"
    friends_only_bool = friends_only_lower in ('true', '1', 'yes', 'on', 't')
    
    # Determine which users' activity to show
    user_ids = None
    if friends_only_bool:
        if not current_user:
            return {
                "items": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0
            }
        # Get list of followed user IDs
        following_result = await db.execute(
            select(Follow.following_id).where(Follow.follower_id == current_user.id)
        )
        user_ids = [row[0] for row in following_result.all()]
        
        if not user_ids:
            return {
                "items": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0
            }
    
    # Collect all activities
    activities = []
    
    # Set reviews
    set_reviews_query = select(Review).where(Review.is_public == True)
    if user_ids:
        set_reviews_query = set_reviews_query.where(Review.user_id.in_(user_ids))
    set_reviews_query = set_reviews_query.order_by(Review.created_at.desc()).limit(limit * 3)
    set_reviews_result = await db.execute(set_reviews_query)
    set_reviews = set_reviews_result.scalars().all()
    
    for review in set_reviews:
        await db.refresh(review, ["user", "set"])
        review_response = ReviewResponse.model_validate(review)
        # Add set data to review response dict
        review_dict = review_response.model_dump()
        if review.set:
            review_dict["set"] = DJSetResponse.model_validate(review.set).model_dump()
        activities.append({
            "activity_type": "set_review",
            "created_at": review.created_at,
            "user": UserResponse.model_validate(review.user).model_dump(),
            "set_review": review_dict,
            "set_rating": None,
            "track_review": None,
            "track_rating": None,
            "top_track": None,
            "top_set": None,
            "event_created": None,
            "event_confirmed": None
        })
    
    # Set ratings
    set_ratings_query = select(Rating)
    if user_ids:
        set_ratings_query = set_ratings_query.where(Rating.user_id.in_(user_ids))
    set_ratings_query = set_ratings_query.order_by(Rating.created_at.desc()).limit(limit * 3)
    set_ratings_result = await db.execute(set_ratings_query)
    set_ratings = set_ratings_result.scalars().all()
    
    for rating in set_ratings:
        await db.refresh(rating, ["user", "set"])
        rating_dict = RatingResponse.model_validate(rating).model_dump()
        rating_dict["set"] = DJSetResponse.model_validate(rating.set).model_dump() if rating.set else None
        activities.append({
            "activity_type": "set_rating",
            "created_at": rating.created_at,
            "user": UserResponse.model_validate(rating.user).model_dump(),
            "set_review": None,
            "set_rating": rating_dict,
            "track_review": None,
            "track_rating": None,
            "top_track": None,
            "top_set": None,
            "event_created": None,
            "event_confirmed": None
        })
    
    # Track reviews
    track_reviews_query = select(TrackReview).where(TrackReview.is_public == True)
    if user_ids:
        track_reviews_query = track_reviews_query.where(TrackReview.user_id.in_(user_ids))
    track_reviews_query = track_reviews_query.order_by(TrackReview.created_at.desc()).limit(limit * 3)
    track_reviews_result = await db.execute(track_reviews_query)
    track_reviews = track_reviews_result.scalars().all()
    
    for review in track_reviews:
        await db.refresh(review, ["user", "track"])
        review_dict = TrackReviewResponse.model_validate(review).model_dump()
        review_dict["track"] = TrackResponse.model_validate(review.track).model_dump() if review.track else None
        activities.append({
            "activity_type": "track_review",
            "created_at": review.created_at,
            "user": UserResponse.model_validate(review.user).model_dump(),
            "set_review": None,
            "set_rating": None,
            "track_review": review_dict,
            "track_rating": None,
            "top_track": None,
            "top_set": None,
            "event_created": None,
            "event_confirmed": None
        })
    
    # Track ratings
    track_ratings_query = select(TrackRating)
    if user_ids:
        track_ratings_query = track_ratings_query.where(TrackRating.user_id.in_(user_ids))
    track_ratings_query = track_ratings_query.order_by(TrackRating.created_at.desc()).limit(limit * 3)
    track_ratings_result = await db.execute(track_ratings_query)
    track_ratings = track_ratings_result.scalars().all()
    
    for rating in track_ratings:
        await db.refresh(rating, ["user", "track"])
        rating_dict = TrackRatingResponse.model_validate(rating).model_dump()
        rating_dict["track"] = TrackResponse.model_validate(rating.track).model_dump() if rating.track else None
        activities.append({
            "activity_type": "track_rating",
            "created_at": rating.created_at,
            "user": UserResponse.model_validate(rating.user).model_dump(),
            "set_review": None,
            "set_rating": None,
            "track_review": None,
            "track_rating": rating_dict,
            "top_track": None,
            "top_set": None,
            "event_created": None,
            "event_confirmed": None
        })
    
    # Top tracks (when users add tracks to their top 5)
    top_tracks_query = select(UserTopTrack)
    if user_ids:
        top_tracks_query = top_tracks_query.where(UserTopTrack.user_id.in_(user_ids))
    top_tracks_query = top_tracks_query.order_by(UserTopTrack.created_at.desc()).limit(limit * 3)
    top_tracks_result = await db.execute(top_tracks_query)
    top_tracks = top_tracks_result.scalars().all()
    
    for top_track in top_tracks:
        await db.refresh(top_track, ["user", "track"])
        activities.append({
            "activity_type": "top_track",
            "created_at": top_track.created_at,
            "user": UserResponse.model_validate(top_track.user).model_dump(),
            "set_review": None,
            "set_rating": None,
            "track_review": None,
            "track_rating": None,
            "top_track": {
                "track": TrackResponse.model_validate(top_track.track).model_dump(),
                "order": top_track.order
            },
            "top_set": None,
            "event_created": None,
            "event_confirmed": None
        })
    
    # Top sets (when users add sets to their top 5)
    # We need to track when is_top_set changes, but since we don't have an update timestamp,
    # we'll use created_at from UserSetLog when is_top_set=True
    top_sets_query = select(UserSetLog).where(UserSetLog.is_top_set == True)
    if user_ids:
        top_sets_query = top_sets_query.where(UserSetLog.user_id.in_(user_ids))
    top_sets_query = top_sets_query.order_by(UserSetLog.created_at.desc()).limit(limit * 3)
    top_sets_result = await db.execute(top_sets_query)
    top_sets = top_sets_result.scalars().all()
    
    for log in top_sets:
        await db.refresh(log, ["user", "set"])
        activities.append({
            "activity_type": "top_set",
            "created_at": log.created_at,
            "user": UserResponse.model_validate(log.user).model_dump(),
            "set_review": None,
            "set_rating": None,
            "track_review": None,
            "track_rating": None,
            "top_track": None,
            "top_set": {
                "set": DJSetResponse.model_validate(log.set).model_dump(),
                "log": LogResponse.model_validate(log).model_dump(),
                "order": log.top_set_order
            },
            "event_created": None,
            "event_confirmed": None
        })
    
    # Event creation (when users create events)
    events_query = select(Event)
    if user_ids:
        events_query = events_query.where(Event.created_by_id.in_(user_ids))
    events_query = events_query.order_by(Event.created_at.desc()).limit(limit * 3)
    events_result = await db.execute(events_query)
    events = events_result.scalars().all()
    
    for event in events:
        await db.refresh(event, ["created_by"])
        activities.append({
            "activity_type": "event_created",
            "created_at": event.created_at,
            "user": UserResponse.model_validate(event.created_by).model_dump(),
            "set_review": None,
            "set_rating": None,
            "track_review": None,
            "track_rating": None,
            "top_track": None,
            "top_set": None,
            "event_created": {
                "event": EventResponse.model_validate(event).model_dump()
            },
            "event_confirmed": None
        })
    
    # Event confirmations (when users confirm they attended events)
    event_confirmations_query = select(EventConfirmation)
    if user_ids:
        event_confirmations_query = event_confirmations_query.where(EventConfirmation.user_id.in_(user_ids))
    event_confirmations_query = event_confirmations_query.order_by(EventConfirmation.created_at.desc()).limit(limit * 3)
    event_confirmations_result = await db.execute(event_confirmations_query)
    event_confirmations = event_confirmations_result.scalars().all()
    
    for confirmation in event_confirmations:
        await db.refresh(confirmation, ["user", "event"])
        activities.append({
            "activity_type": "event_confirmed",
            "created_at": confirmation.created_at,
            "user": UserResponse.model_validate(confirmation.user).model_dump(),
            "set_review": None,
            "set_rating": None,
            "track_review": None,
            "track_rating": None,
            "top_track": None,
            "top_set": None,
            "event_created": None,
            "event_confirmed": {
                "event": EventResponse.model_validate(confirmation.event).model_dump()
            }
        })
    
    # Sort all activities by created_at (most recent first)
    activities.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply pagination
    total = len(activities)
    offset = (page - 1) * limit
    paginated_activities = activities[offset:offset + limit]
    
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    # Return as dict for now to debug
    return {
        "items": paginated_activities,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }


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


@router.get("/{user_id}/top-events", response_model=list)
async def get_user_top_events(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a user's top 5 events (same pattern as top tracks)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    query = (
        select(Event, UserTopEvent.order)
        .join(UserTopEvent, Event.id == UserTopEvent.event_id)
        .where(UserTopEvent.user_id == user_id)
        .order_by(UserTopEvent.order.asc())
        .limit(5)
    )
    result = await db.execute(query)
    rows = result.all()
    return [
        {**EventResponse.model_validate(e).model_dump(), "order": order}
        for e, order in rows
    ]


@router.get("/{user_id}/top-venues", response_model=list)
async def get_user_top_venues(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a user's top 5 venues (same pattern as top tracks)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    query = (
        select(Venue, UserTopVenue.order, UserTopVenue.id.label("user_top_venue_id"))
        .join(UserTopVenue, Venue.id == UserTopVenue.venue_id)
        .where(UserTopVenue.user_id == user_id)
        .order_by(UserTopVenue.order.asc())
        .limit(5)
    )
    result = await db.execute(query)
    rows = result.all()
    return [
        {**VenueResponse.model_validate(venue).model_dump(), "order": order, "id": str(user_top_venue_id)}
        for venue, order, user_top_venue_id in rows
    ]


@router.post("/me/top-events", status_code=status.HTTP_201_CREATED)
async def add_top_event(
    event_id: UUID = Query(...),
    order: int = Query(..., ge=1, le=5),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add an event to current user's top 5 (same pattern as top tracks)."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    # If already at this order or event already in top 5, replace
    existing = await db.execute(
        select(UserTopEvent).where(
            UserTopEvent.user_id == current_user.id,
            (UserTopEvent.event_id == event_id) | (UserTopEvent.order == order)
        )
    )
    for row in existing.scalars().all():
        await db.delete(row)
    db.add(UserTopEvent(user_id=current_user.id, event_id=event_id, order=order))
    await db.commit()
    return {"event_id": str(event_id), "order": order}


@router.delete("/me/top-events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_top_event(
    event_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove an event from current user's top 5."""
    result = await db.execute(
        select(UserTopEvent).where(
            UserTopEvent.user_id == current_user.id,
            UserTopEvent.event_id == event_id
        )
    )
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()
    return None


@router.post("/me/top-venues", status_code=status.HTTP_201_CREATED)
async def add_top_venue(
    venue_id: UUID = Query(..., description="Venue UUID from /api/venues"),
    order: int = Query(..., ge=1, le=5),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a venue to current user's top 5."""
    result = await db.execute(select(Venue).where(Venue.id == venue_id))
    venue = result.scalar_one_or_none()
    if not venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")
    existing = await db.execute(
        select(UserTopVenue).where(
            UserTopVenue.user_id == current_user.id,
            (UserTopVenue.venue_id == venue_id) | (UserTopVenue.order == order)
        )
    )
    for row in existing.scalars().all():
        await db.delete(row)
    db.add(UserTopVenue(user_id=current_user.id, venue_id=venue_id, order=order))
    await db.commit()
    return {"venue_id": str(venue_id), "order": order}


@router.delete("/me/top-venues/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_top_venue(
    venue_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a venue from current user's top 5 by UserTopVenue id."""
    result = await db.execute(
        select(UserTopVenue).where(
            UserTopVenue.id == venue_id,
            UserTopVenue.user_id == current_user.id
        )
    )
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()
    return None


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
    Get activity feed from users that the current user follows (friends-only).
    
    This is a convenience endpoint that calls activity-feed with friends_only=True.
    """
    return await get_activity_feed(page=page, limit=limit, friends_only=True, current_user=current_user, db=db)


