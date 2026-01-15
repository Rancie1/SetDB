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
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


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
    is_reviewed: bool
    created_at: datetime


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


# ============================================================================
# LIST SCHEMAS
# ============================================================================

class ListCreate(BaseSchema):
    """Schema for creating a list."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: bool = True


class ListUpdate(BaseSchema):
    """Schema for updating a list."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class ListItemCreate(BaseSchema):
    """Schema for adding a set to a list."""
    set_id: UUID
    position: Optional[int] = None  # If None, append to end
    notes: Optional[str] = None


class ListItemUpdate(BaseSchema):
    """Schema for updating a list item."""
    position: Optional[int] = None
    notes: Optional[str] = None


class ListItemResponse(BaseSchema):
    """Schema for list item response."""
    id: UUID
    list_id: UUID
    set_id: UUID
    position: int
    notes: Optional[str] = None
    created_at: datetime
    set: Optional[DJSetResponse] = None


class ListResponse(BaseSchema):
    """Schema for list response."""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    is_public: bool
    is_featured: bool
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
    venue_location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None


class EventResponse(EventBase):
    """Schema for event response."""
    id: UUID
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
