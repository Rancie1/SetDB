"""
Pydantic schemas for request/response validation.

This module defines schemas for:
- Request validation (what the API receives)
- Response validation (what the API returns)
- Update schemas (partial updates)

Why separate schemas?
- Security: Never expose internal fields (like hashed_password)
- Validation: Ensure data integrity before database operations
- Documentation: Auto-generated API docs show expected formats
- Flexibility: Different schemas for different endpoints
"""

from datetime import datetime, date
from typing import Optional, List, Any, TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

if TYPE_CHECKING:
    # Forward references for types defined later in this file
    pass


# Base schemas with common fields
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(from_attributes=True)  # Allows conversion from ORM models


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseSchema):
    """Base user schema with common fields."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseSchema):
    """Schema for updating user (all fields optional)."""
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response (what we return to clients)."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Note: hashed_password is NOT included - security!


# ============================================================================
# DJ SET SCHEMAS
# ============================================================================

class DJSetBase(BaseSchema):
    """Base DJ set schema."""
    title: str = Field(..., min_length=1, max_length=255)
    dj_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=0)


class DJSetCreate(DJSetBase):
    """Schema for creating a DJ set (manual entry)."""
    source_type: str = Field(..., pattern="^(youtube|soundcloud|live)$")
    source_url: str = Field(..., max_length=500)
    event_name: Optional[str] = None
    event_date: Optional[date] = None
    venue_location: Optional[str] = None
    recording_url: Optional[str] = Field(None, max_length=500)  # For live sets with recordings


class DJSetUpdate(BaseSchema):
    """Schema for updating a DJ set."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    dj_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    recording_url: Optional[str] = Field(None, max_length=500)


class DJSetResponse(DJSetBase):
    """Schema for DJ set response."""
    id: UUID
    source_type: str
    source_id: Optional[str] = None
    source_url: str
    recording_url: Optional[str] = None
    extra_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    created_by_id: UUID


# ============================================================================
# LOG SCHEMAS
# ============================================================================

class LogCreate(BaseSchema):
    """Schema for logging a set."""
    set_id: UUID
    watched_date: date


class LogUpdate(BaseSchema):
    """Schema for updating a log."""
    watched_date: Optional[date] = None


class LogResponse(BaseSchema):
    """Schema for log response."""
    id: UUID
    user_id: UUID
    set_id: UUID
    watched_date: date
    is_top_set: Optional[bool] = False
    top_set_order: Optional[int] = None
    is_reviewed: bool
    created_at: datetime
    # Include set info for display (will be populated by API)
    set: Optional[Any] = None


# ============================================================================
# RATING SCHEMAS
# ============================================================================

class RatingCreate(BaseSchema):
    """Schema for creating a rating."""
    set_id: UUID
    rating: float = Field(..., ge=0.5, le=5.0)


class RatingUpdate(BaseSchema):
    """Schema for updating a rating."""
    rating: float = Field(..., ge=0.5, le=5.0)


class RatingResponse(BaseSchema):
    """Schema for rating response."""
    id: UUID
    user_id: UUID
    set_id: UUID
    rating: float
    created_at: datetime
    updated_at: datetime


class RatingStats(BaseSchema):
    """Schema for rating statistics."""
    average_rating: Optional[float] = None
    total_ratings: int
    rating_distribution: dict  # {0.5: 5, 1.0: 10, ...}


# ============================================================================
# REVIEW SCHEMAS
# ============================================================================

class ReviewCreate(BaseSchema):
    """Schema for creating a review."""
    set_id: UUID
    content: str = Field(..., min_length=1)
    contains_spoilers: bool = False
    is_public: bool = True


class ReviewUpdate(BaseSchema):
    """Schema for updating a review."""
    content: Optional[str] = Field(None, min_length=1)
    contains_spoilers: Optional[bool] = None
    is_public: Optional[bool] = None


class ReviewResponse(BaseSchema):
    """Schema for review response."""
    id: UUID
    user_id: UUID
    set_id: UUID
    content: str
    contains_spoilers: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime
    # Include user info for display
    user: Optional[UserResponse] = None
    # Include the user's rating for this set (if they have one)
    user_rating: Optional[float] = None


# ============================================================================
# TRACK TAG SCHEMAS
# ============================================================================

class SetTrackCreate(BaseSchema):
    """Schema for creating a track tag."""
    track_id: Optional[UUID] = Field(None, description="Optional: ID of existing Track entity to link. If provided, track_name/artist_name are optional.")
    track_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Required if track_id not provided")
    artist_name: Optional[str] = Field(None, max_length=255)
    soundcloud_url: Optional[str] = Field(None, max_length=500)
    position: Optional[int] = Field(None, ge=0)
    timestamp_minutes: Optional[float] = Field(None, ge=0, description="Timestamp in minutes for sets with recordings")


class SetTrackUpdate(BaseSchema):
    """Schema for updating a track tag."""
    track_name: Optional[str] = Field(None, min_length=1, max_length=255)
    artist_name: Optional[str] = Field(None, max_length=255)
    soundcloud_url: Optional[str] = Field(None, max_length=500)
    position: Optional[int] = Field(None, ge=0)
    timestamp_minutes: Optional[float] = Field(None, ge=0, description="Timestamp in minutes for sets with recordings")


class SetTrackResponse(BaseSchema):
    """Schema for track tag response."""
    id: UUID
    set_id: UUID
    added_by_id: UUID
    track_name: str
    artist_name: Optional[str] = None
    soundcloud_url: Optional[str] = None
    soundcloud_track_id: Optional[str] = None
    position: Optional[int] = None
    timestamp_minutes: Optional[float] = None
    is_top_track: Optional[bool] = False
    top_track_order: Optional[int] = None
    created_at: datetime
    # Include user info for display
    added_by: Optional[UserResponse] = None
    # Confirmation stats
    confirmation_count: Optional[int] = 0
    denial_count: Optional[int] = 0
    user_confirmation: Optional[bool] = None  # Current user's confirmation status
    supports_confirmations: Optional[bool] = True  # Whether this track supports confirmations (SetTrack = True, TrackSetLink = False)
    # Rating stats
    average_rating: Optional[float] = None
    rating_count: Optional[int] = 0
    user_rating: Optional[float] = None  # Current user's rating


class TrackConfirmationCreate(BaseSchema):
    """Schema for creating a track confirmation."""
    is_confirmed: bool = Field(..., description="True if track is correct, False if incorrect")


class TrackConfirmationResponse(BaseSchema):
    """Schema for track confirmation response."""
    id: UUID
    track_id: Optional[UUID] = None  # For SetTrack entries
    track_set_link_id: Optional[UUID] = None  # For TrackSetLink entries
    user_id: UUID
    is_confirmed: bool
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None


# ============================================================================
# TRACK SCHEMAS (Independent Track Entity)
# ============================================================================

class TrackCreate(BaseSchema):
    """Schema for creating an independent track."""
    track_name: str = Field(..., min_length=1, max_length=255)
    artist_name: Optional[str] = Field(None, max_length=255)
    soundcloud_url: Optional[str] = Field(None, max_length=500)
    soundcloud_track_id: Optional[str] = Field(None, max_length=255)
    spotify_url: Optional[str] = Field(None, max_length=500)
    spotify_track_id: Optional[str] = Field(None, max_length=255)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    duration_ms: Optional[int] = None


class TrackResponse(BaseSchema):
    """Schema for track response."""
    id: UUID
    track_name: str
    artist_name: Optional[str] = None
    soundcloud_url: Optional[str] = None
    soundcloud_track_id: Optional[str] = None
    spotify_url: Optional[str] = None
    spotify_track_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_ms: Optional[int] = None
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    # Stats
    average_rating: Optional[float] = None
    rating_count: Optional[int] = 0
    user_rating: Optional[float] = None  # Current user's rating
    linked_sets_count: Optional[int] = 0
    is_top_track: Optional[bool] = False
    top_track_order: Optional[int] = None


class TrackSetLinkCreate(BaseSchema):
    """Schema for linking a track to a set."""
    set_id: UUID
    position: Optional[int] = None
    timestamp_minutes: Optional[float] = None


class TrackSetLinkResponse(BaseSchema):
    """Schema for track-set link response."""
    id: UUID
    track_id: UUID
    set_id: UUID
    added_by_id: UUID
    position: Optional[int] = None
    timestamp_minutes: Optional[float] = None
    created_at: datetime
    track: Optional[TrackResponse] = None
    set: Optional[DJSetResponse] = None


# ============================================================================
# TRACK RATING SCHEMAS
# ============================================================================

class TrackRatingCreate(BaseSchema):
    """Schema for creating a track rating."""
    track_id: UUID
    rating: float = Field(..., ge=0.5, le=5.0, description="Rating from 0.5 to 5.0 stars")


class TrackRatingUpdate(BaseSchema):
    """Schema for updating a track rating."""
    rating: float = Field(..., ge=0.5, le=5.0, description="Rating from 0.5 to 5.0 stars")


class TrackRatingResponse(BaseSchema):
    """Schema for track rating response."""
    id: UUID
    user_id: UUID
    track_id: UUID
    rating: float
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None


# ============================================================================
# TRACK REVIEW SCHEMAS
# ============================================================================

class TrackReviewCreate(BaseSchema):
    """Schema for creating a track review."""
    track_id: UUID
    content: str = Field(..., min_length=1)
    contains_spoilers: bool = False
    is_public: bool = True


class TrackReviewUpdate(BaseSchema):
    """Schema for updating a track review."""
    content: Optional[str] = Field(None, min_length=1)
    contains_spoilers: Optional[bool] = None
    is_public: Optional[bool] = None


class TrackReviewResponse(BaseSchema):
    """Schema for track review response."""
    id: UUID
    user_id: UUID
    track_id: UUID
    content: str
    contains_spoilers: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None
    user_rating: Optional[float] = None




# ============================================================================
# LIST SCHEMAS
# ============================================================================

class ListCreate(BaseSchema):
    """Schema for creating a list."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    list_type: str = Field(..., pattern="^(sets|events|venues|tracks)$", description="Type of list: sets, events, venues, or tracks")
    is_public: bool = True
    max_items: Optional[int] = Field(None, ge=1, le=100, description="Maximum number of items (default 5 for top 5 lists)")


class ListUpdate(BaseSchema):
    """Schema for updating a list."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: Optional[bool] = None
    max_items: Optional[int] = Field(None, ge=1, le=100)


class ListItemCreate(BaseSchema):
    """Schema for adding an item to a list (polymorphic)."""
    # One of these must be provided based on list type
    set_id: Optional[UUID] = None
    event_id: Optional[UUID] = None
    track_id: Optional[UUID] = None
    venue_name: Optional[str] = Field(None, max_length=255)
    position: Optional[int] = Field(None, ge=1)  # If None, append to end
    notes: Optional[str] = None


class ListItemUpdate(BaseSchema):
    """Schema for updating a list item."""
    position: Optional[int] = None
    notes: Optional[str] = None


class ListItemResponse(BaseSchema):
    """Schema for list item response (polymorphic)."""
    id: UUID
    list_id: UUID
    set_id: Optional[UUID] = None
    event_id: Optional[UUID] = None
    track_id: Optional[UUID] = None
    venue_name: Optional[str] = None
    position: int
    notes: Optional[str] = None
    created_at: datetime
    # Item data (one will be populated based on type)
    # Using string literals for forward references since these classes are defined later
    set: Optional["DJSetResponse"] = None
    event: Optional["EventResponse"] = None
    track: Optional["TrackResponse"] = None


class ListResponse(BaseSchema):
    """Schema for list response."""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    list_type: str
    is_public: bool
    is_featured: bool
    max_items: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None
    items: Optional[List[ListItemResponse]] = None


# ============================================================================
# FOLLOW SCHEMAS
# ============================================================================

class FollowResponse(BaseSchema):
    """Schema for follow relationship."""
    id: UUID
    follower_id: UUID
    following_id: UUID
    created_at: datetime
    follower: Optional[UserResponse] = None
    following: Optional[UserResponse] = None


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class Token(BaseSchema):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseSchema):
    """Schema for token data."""
    user_id: Optional[UUID] = None


# ============================================================================
# STATS SCHEMAS
# ============================================================================

class UserStats(BaseSchema):
    """Schema for user statistics."""
    sets_logged: int
    reviews_written: int
    lists_created: int
    average_rating: Optional[float] = None
    following_count: int
    followers_count: int
    hours_listened: float = 0.0
    venues_attended: int = 0


# ============================================================================
# PAGINATION SCHEMAS
# ============================================================================

class PaginatedResponse(BaseModel):
    """Base schema for paginated responses."""
    items: List[Any]  # Can be any Pydantic model
    total: int
    page: int
    limit: int
    pages: int
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ACTIVITY FEED SCHEMAS
# ============================================================================

class ActivityItem(BaseSchema):
    """Schema for activity feed items."""
    activity_type: str  # "set_review", "set_rating", "track_review", "track_rating", "top_track", "top_set", "event_created", "event_confirmed"
    created_at: datetime
    user: UserResponse
    
    # Activity-specific data (one of these will be populated based on activity_type)
    set_review: Optional[ReviewResponse] = None
    set_rating: Optional[RatingResponse] = None
    track_review: Optional[TrackReviewResponse] = None
    track_rating: Optional[TrackRatingResponse] = None
    top_track: Optional[dict] = None  # {track: TrackResponse, order: int}
    top_set: Optional[dict] = None  # {set: DJSetResponse, log: LogResponse, order: int}
    event_created: Optional[dict] = None  # {event: EventResponse}
    event_confirmed: Optional[dict] = None  # {event: EventResponse}


# ============================================================================
# IMPORT SCHEMAS
# ============================================================================

class ImportSetRequest(BaseSchema):
    """Schema for importing a set from external source."""
    url: str = Field(..., min_length=1, max_length=500)
    mark_as_live: bool = Field(False, description="If True, create as a live set with the imported URL as recording_url")


# ============================================================================
# EVENT SCHEMAS
# ============================================================================

class EventBase(BaseSchema):
    """Base event schema."""
    title: str = Field(..., min_length=1, max_length=255)
    dj_name: str = Field(..., min_length=1, max_length=255)
    event_name: Optional[str] = Field(None, max_length=255)
    event_date: Optional[date] = None
    duration_days: Optional[int] = Field(None, ge=1, description="Event length in days")
    venue_location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None


class EventCreate(EventBase):
    """Schema for creating an event."""
    pass


class EventUpdate(BaseSchema):
    """Schema for updating an event."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    dj_name: Optional[str] = Field(None, min_length=1, max_length=255)
    event_name: Optional[str] = Field(None, max_length=255)
    event_date: Optional[date] = None
    duration_days: Optional[int] = Field(None, ge=1, description="Event length in days")
    venue_location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None


class EventResponse(EventBase):
    """Schema for event response."""
    id: UUID


# Update forward references after all classes are defined
if not TYPE_CHECKING:
    ListItemResponse.model_rebuild()
    is_verified: bool = False
    confirmation_count: int = 0
    created_at: datetime
    updated_at: datetime
    created_by_id: UUID


class CreateLiveEventFromSetRequest(BaseSchema):
    """Schema for creating a live event from an existing set."""
    event_name: Optional[str] = Field(None, max_length=255)
    event_date: Optional[date] = None
    venue_location: Optional[str] = Field(None, max_length=255)
