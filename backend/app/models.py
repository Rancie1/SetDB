"""
Database models (SQLAlchemy ORM).

This module defines all database tables as SQLAlchemy models.
Each model represents a table in the PostgreSQL database.
"""

from __future__ import annotations

from datetime import datetime
from typing import List as _List, Optional
from uuid import uuid4

from sqlalchemy import String, Text, Boolean, Integer, Float, Date, DateTime, ForeignKey, Enum, UniqueConstraint, CheckConstraint, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
import enum


class SourceType(str, enum.Enum):
    """Enum for DJ set source types."""
    YOUTUBE = "youtube"
    SOUNDCLOUD = "soundcloud"
    LIVE = "live"


class ListType(str, enum.Enum):
    """Enum for list types/categories."""
    SETS = "sets"
    EVENTS = "events"
    VENUES = "venues"
    TRACKS = "tracks"


class User(Base):
    """
    User model - stores user accounts and profiles.
    
    This is the main user table. Users can log sets, write reviews,
    create lists, and follow other users.
    """
    __tablename__ = "users"
    
    # Primary key - UUID for better security and distributed systems
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Authentication fields
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Nullable for OAuth users
    
    # OAuth fields
    soundcloud_user_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    soundcloud_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Encrypted in production
    soundcloud_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Google OAuth fields
    google_user_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    google_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    google_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    google_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Profile fields
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    # These allow us to access related data easily (e.g., user.reviews)
    reviews: Mapped["_List[Review]"] = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    ratings: Mapped["_List[Rating]"] = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    logs: Mapped["_List[UserSetLog]"] = relationship("UserSetLog", back_populates="user", cascade="all, delete-orphan")
    created_sets: Mapped["_List[DJSet]"] = relationship("DJSet", back_populates="created_by", foreign_keys="DJSet.created_by_id")
    created_events: Mapped["_List[Event]"] = relationship("Event", back_populates="created_by", foreign_keys="Event.created_by_id")
    lists: Mapped["_List[List]"] = relationship("List", back_populates="user", cascade="all, delete-orphan")
    
    # Following relationships
    following: Mapped["_List[Follow]"] = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan"
    )
    followers: Mapped["_List[Follow]"] = relationship(
        "Follow",
        foreign_keys="Follow.following_id",
        back_populates="following",
        cascade="all, delete-orphan"
    )
    event_confirmations: Mapped["_List[EventConfirmation]"] = relationship(
        "EventConfirmation",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    track_ratings: Mapped["_List[TrackRating]"] = relationship("TrackRating", back_populates="user", cascade="all, delete-orphan")
    track_reviews: Mapped["_List[TrackReview]"] = relationship("TrackReview", back_populates="user", cascade="all, delete-orphan")
    top_tracks: Mapped["_List[UserTopTrack]"] = relationship("UserTopTrack", back_populates="user", cascade="all, delete-orphan")
    top_events: Mapped["_List[UserTopEvent]"] = relationship("UserTopEvent", back_populates="user", cascade="all, delete-orphan")
    top_venues: Mapped["_List[UserTopVenue]"] = relationship("UserTopVenue", back_populates="user", cascade="all, delete-orphan")


class DJSet(Base):
    """
    DJ Set model - stores DJ set information from all sources.
    
    Sets can come from YouTube, SoundCloud, or be manually entered
    for live events. The metadata field stores platform-specific data.
    """
    __tablename__ = "dj_sets"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Basic information
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    dj_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    
    # Source information
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False, index=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    
    # Media information
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Recording URL for live sets (YouTube/SoundCloud recording if available)
    # This stores the URL of the recording if the set was imported and marked as live
    recording_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Additional information
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Platform-specific data
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Foreign keys
    created_by_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id], back_populates="created_sets")
    reviews: Mapped["_List[Review]"] = relationship("Review", back_populates="set", cascade="all, delete-orphan")
    ratings: Mapped["_List[Rating]"] = relationship("Rating", back_populates="set", cascade="all, delete-orphan")
    logs: Mapped["_List[UserSetLog]"] = relationship("UserSetLog", back_populates="set", cascade="all, delete-orphan")
    list_items: Mapped["_List[ListItem]"] = relationship("ListItem", back_populates="set", cascade="all, delete-orphan")
    
    # Relationships for events (many-to-many via EventSet table)
    event_sets: Mapped["_List[EventSet]"] = relationship("EventSet", foreign_keys="EventSet.set_id", back_populates="set", cascade="all, delete-orphan")
    
    # Relationships for track tags
    track_tags: Mapped["_List[SetTrack]"] = relationship("SetTrack", back_populates="set", cascade="all, delete-orphan")
    track_links: Mapped["_List[TrackSetLink]"] = relationship("TrackSetLink", back_populates="set", cascade="all, delete-orphan")
    list_items: Mapped["_List[ListItem]"] = relationship("ListItem", back_populates="set", cascade="all, delete-orphan", foreign_keys="ListItem.set_id")
    
    # Unique constraint: prevent duplicate sets from same source
    __table_args__ = (
        UniqueConstraint('source_type', 'source_id', name='uq_set_source'),
    )


class SetTrack(Base):
    """
    Set Track model - tracks individual songs/tracks played in a set.
    
    Users can tag tracks that were played in a set. If the track is available
    on SoundCloud, a link is provided to access it.
    """
    __tablename__ = "set_tracks"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    set_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dj_sets.id"), nullable=False, index=True)
    added_by_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Track information
    track_name: Mapped[str] = mapped_column(String(255), nullable=False)
    artist_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # SoundCloud link (if available)
    soundcloud_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    soundcloud_track_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Position in set (optional - for ordering tracks)
    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamp in recording (in minutes) - for sets with recordings
    timestamp_minutes: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Top tracks feature - users can mark tracks as their favorites
    is_top_track: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    top_track_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 for ordering top tracks
    
    # Relationships
    set: Mapped["DJSet"] = relationship("DJSet", back_populates="track_tags")
    added_by: Mapped["User"] = relationship("User", foreign_keys=[added_by_id])
    confirmations: Mapped["_List[TrackConfirmation]"] = relationship("TrackConfirmation", back_populates="track", cascade="all, delete-orphan")
    # Note: TrackRating and TrackReview now reference Track model, not SetTrack
    
    # Unique constraint: prevent duplicate track tags for same set
    __table_args__ = (
        UniqueConstraint('set_id', 'track_name', 'artist_name', name='uq_set_track'),
    )


class Track(Base):
    """
    Track model - independent track entity from SoundCloud or other sources.
    
    Tracks can exist independently and be linked to multiple sets.
    This is separate from SetTrack which represents a track's appearance in a specific set.
    """
    __tablename__ = "tracks"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Track information
    track_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    artist_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # SoundCloud information
    soundcloud_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, unique=True)
    soundcloud_track_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    
    # Spotify information
    spotify_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, unique=True)
    spotify_track_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    
    # Common metadata
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Metadata
    created_by_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])
    set_links: Mapped["_List[TrackSetLink]"] = relationship("TrackSetLink", back_populates="track", cascade="all, delete-orphan")
    ratings: Mapped["_List[TrackRating]"] = relationship("TrackRating", back_populates="track", cascade="all, delete-orphan")
    reviews: Mapped["_List[TrackReview]"] = relationship("TrackReview", back_populates="track", cascade="all, delete-orphan")
    user_top_tracks: Mapped["_List[UserTopTrack]"] = relationship("UserTopTrack", back_populates="track", cascade="all, delete-orphan")
    list_items: Mapped["_List[ListItem]"] = relationship("ListItem", back_populates="track", cascade="all, delete-orphan", foreign_keys="ListItem.track_id")


class TrackSetLink(Base):
    """
    Track-Set Link model - links tracks to sets (many-to-many).
    
    Represents that a track appears in a set, with optional metadata like timestamp.
    """
    __tablename__ = "track_set_links"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    track_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tracks.id"), nullable=False, index=True)
    set_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dj_sets.id"), nullable=False, index=True)
    added_by_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Set-specific metadata
    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timestamp_minutes: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    track: Mapped["Track"] = relationship("Track", back_populates="set_links")
    set: Mapped["DJSet"] = relationship("DJSet", back_populates="track_links")
    added_by: Mapped["User"] = relationship("User", foreign_keys=[added_by_id])
    confirmations: Mapped["_List[TrackConfirmation]"] = relationship("TrackConfirmation", foreign_keys="TrackConfirmation.track_set_link_id", back_populates="track_set_link", cascade="all, delete-orphan")
    
    # Unique constraint: prevent duplicate links
    __table_args__ = (
        UniqueConstraint('track_id', 'set_id', name='uq_track_set_link'),
    )


class TrackConfirmation(Base):
    """
    Track Confirmation model - allows users to confirm or deny if a track tag is correct.
    
    Users can vote on whether a track tag accurately represents what was played in the set.
    Supports both SetTrack (manually tagged) and TrackSetLink (linked tracks).
    """
    __tablename__ = "track_confirmations"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys - one of these must be set
    track_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("set_tracks.id"), nullable=True, index=True)
    track_set_link_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("track_set_links.id"), nullable=True, index=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Confirmation status: True = confirmed (correct), False = denied (incorrect)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    track: Mapped[Optional["SetTrack"]] = relationship("SetTrack", back_populates="confirmations", foreign_keys=[track_id])
    track_set_link: Mapped[Optional["TrackSetLink"]] = relationship("TrackSetLink", foreign_keys=[track_set_link_id])
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    
    # Unique constraints: user can only confirm/deny a track once (for each type)
    __table_args__ = (
        UniqueConstraint('user_id', 'track_id', name='uq_user_set_track_confirmation'),
        UniqueConstraint('user_id', 'track_set_link_id', name='uq_user_track_set_link_confirmation'),
    )


class UserSetLog(Base):
    """
    User Set Log - tracks when users log/view sets (like Letterboxd's diary).
    
    This is a many-to-many relationship between users and sets.
    Users can log a set to track that they've watched/listened to it.
    """
    __tablename__ = "user_set_logs"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    set_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dj_sets.id"), nullable=False, index=True)
    
    # Log information
    watched_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Top sets feature - users can mark sets as their top 5
    is_top_set: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    top_set_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 for ordering top sets
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="logs")
    set: Mapped["DJSet"] = relationship("DJSet", back_populates="logs")
    
    # Unique constraint: user can only log a set once
    __table_args__ = (
        UniqueConstraint('user_id', 'set_id', name='uq_user_set_log'),
    )


class Rating(Base):
    """
    Rating model - stores user ratings (0.5 to 5 stars, like Letterboxd).
    
    Users can rate sets with half-star increments from 0.5 to 5.0.
    """
    __tablename__ = "ratings"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    set_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dj_sets.id"), nullable=False, index=True)
    
    # Rating value (0.5, 1.0, 1.5, ..., 5.0)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="ratings")
    set: Mapped["DJSet"] = relationship("DJSet", back_populates="ratings")
    
    # Unique constraint: one rating per user per set
    __table_args__ = (
        UniqueConstraint('user_id', 'set_id', name='uq_user_set_rating'),
    )


class Review(Base):
    """
    Review model - user-written reviews for sets.
    
    Users can write reviews for sets they've logged. Reviews are optional
    and separate from ratings (users can rate without reviewing).
    """
    __tablename__ = "reviews"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    set_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dj_sets.id"), nullable=False, index=True)
    
    # Review content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    contains_spoilers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reviews")
    set: Mapped["DJSet"] = relationship("DJSet", back_populates="reviews")
    
    # Unique constraint: one review per user per set
    __table_args__ = (
        UniqueConstraint('user_id', 'set_id', name='uq_user_set_review'),
    )


class UserTopTrack(Base):
    """
    User Top Track model - users can mark up to 5 tracks as their favorites.
    """
    __tablename__ = "user_top_tracks"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    track_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tracks.id"), nullable=False, index=True)
    
    # Order (1-5)
    order: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 for ordering top tracks
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="top_tracks")
    track: Mapped["Track"] = relationship("Track", back_populates="user_top_tracks")
    
    # Unique constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'track_id', name='uq_user_top_track'),
        UniqueConstraint('user_id', 'order', name='uq_user_top_track_order'),
    )


class UserTopEvent(Base):
    """
    User Top Event - users can mark up to 5 events as their favorites (same pattern as top tracks/sets).
    """
    __tablename__ = "user_top_events"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    user: Mapped["User"] = relationship("User", back_populates="top_events")
    event: Mapped["Event"] = relationship("Event", back_populates="user_top_events")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'event_id', name='uq_user_top_event'),
        UniqueConstraint('user_id', 'order', name='uq_user_top_event_order'),
    )


class Venue(Base):
    """
    Venue model - first-class entity like Event/Track that can be ranked in top 5.
    """
    __tablename__ = "venues"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    user_top_venues: Mapped["_List[UserTopVenue]"] = relationship("UserTopVenue", back_populates="venue", cascade="all, delete-orphan")


class UserTopVenue(Base):
    """
    User Top Venue - users can rank up to 5 venues (same pattern as top tracks/events).
    """
    __tablename__ = "user_top_venues"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    venue_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    user: Mapped["User"] = relationship("User", back_populates="top_venues")
    venue: Mapped["Venue"] = relationship("Venue", back_populates="user_top_venues")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'venue_id', name='uq_user_top_venue'),
        UniqueConstraint('user_id', 'order', name='uq_user_top_venue_order'),
    )


class TrackRating(Base):
    """
    Track Rating model - stores user ratings for individual tracks.
    
    Users can rate tracks with half-star increments from 0.5 to 5.0.
    """
    __tablename__ = "track_ratings"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    track_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tracks.id"), nullable=False, index=True)
    
    # Rating value (0.5, 1.0, 1.5, ..., 5.0)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="track_ratings")
    track: Mapped["Track"] = relationship("Track", back_populates="ratings")
    
    # Unique constraint: one rating per user per track
    __table_args__ = (
        UniqueConstraint('user_id', 'track_id', name='uq_user_track_rating'),
    )


class TrackReview(Base):
    """
    Track Review model - user-written reviews for individual tracks.
    
    Users can write reviews for tracks. Reviews are optional
    and separate from ratings (users can rate without reviewing).
    """
    __tablename__ = "track_reviews"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    track_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tracks.id"), nullable=False, index=True)
    
    # Review content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    contains_spoilers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="track_reviews")
    track: Mapped["Track"] = relationship("Track", back_populates="reviews")
    
    # Unique constraint: one review per user per track
    __table_args__ = (
        UniqueConstraint('user_id', 'track_id', name='uq_user_track_review'),
    )


class List(Base):
    """
    List model - user-created lists (e.g., "Best Techno Sets 2024", "Top 5 Venues").
    
    Users can create lists to organize sets, events, venues, tracks, etc.
    Lists can be public or private and have a maximum of 5 items for "top 5" lists.
    """
    __tablename__ = "lists"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # List information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    list_type: Mapped[ListType] = mapped_column(Enum(ListType, native_enum=False), nullable=False, default=ListType.SETS, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    max_items: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=5)  # For top 5 lists
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="lists")
    items: Mapped["_List[ListItem]"] = relationship("ListItem", back_populates="list", cascade="all, delete-orphan", order_by="ListItem.position")


class ListItem(Base):
    """
    List Item model - items included in lists (polymorphic).
    
    Supports different item types: sets, events, venues (as strings), tracks.
    The position field allows ordered lists (1-5 for top 5 lists).
    """
    __tablename__ = "list_items"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    list_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lists.id"), nullable=False, index=True)
    
    # Polymorphic foreign keys - one of these will be set based on list type
    set_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("dj_sets.id"), nullable=True, index=True)
    event_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=True, index=True)
    track_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tracks.id"), nullable=True, index=True)
    venue_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # For venue lists (stored as string)
    
    # Item information
    position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    list: Mapped["List"] = relationship("List", back_populates="items")
    set: Mapped[Optional["DJSet"]] = relationship("DJSet", back_populates="list_items", foreign_keys=[set_id])
    event: Mapped[Optional["Event"]] = relationship("Event", foreign_keys=[event_id])
    track: Mapped[Optional["Track"]] = relationship("Track", foreign_keys=[track_id])
    
    # Unique constraints: prevent duplicates in same list for each type
    __table_args__ = (
        UniqueConstraint('list_id', 'set_id', name='uq_list_set_item'),
        UniqueConstraint('list_id', 'event_id', name='uq_list_event_item'),
        UniqueConstraint('list_id', 'track_id', name='uq_list_track_item'),
        UniqueConstraint('list_id', 'venue_name', name='uq_list_venue_item'),
        CheckConstraint(
            '(set_id IS NOT NULL)::int + (event_id IS NOT NULL)::int + (track_id IS NOT NULL)::int + (venue_name IS NOT NULL)::int = 1',
            name='check_exactly_one_item_type'
        ),
    )


class Follow(Base):
    """
    Follow model - user following relationships.
    
    This tracks which users follow which other users.
    """
    __tablename__ = "follows"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    follower_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    following_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    follower: Mapped["User"] = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following: Mapped["User"] = relationship("User", foreign_keys=[following_id], back_populates="followers")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id', name='uq_follow'),
        CheckConstraint('follower_id != following_id', name='check_no_self_follow'),
    )


class Event(Base):
    """
    Event model - stores live event information.
    
    Events are separate from sets. Users can attend events and confirm they happened.
    Sets can be linked to events via the EventSet many-to-many table.
    """
    __tablename__ = "events"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Basic information
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    dj_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    
    # Event information
    event_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    event_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True, index=True)
    duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    venue_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Media information
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Verification fields
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    confirmation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Foreign keys
    created_by_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id], back_populates="created_events")
    linked_sets: Mapped["_List[EventSet]"] = relationship("EventSet", foreign_keys="EventSet.event_id", back_populates="event", cascade="all, delete-orphan")
    confirmations: Mapped["_List[EventConfirmation]"] = relationship("EventConfirmation", back_populates="event", cascade="all, delete-orphan")
    list_items: Mapped["_List[ListItem]"] = relationship("ListItem", back_populates="event", cascade="all, delete-orphan", foreign_keys="ListItem.event_id")
    user_top_events: Mapped["_List[UserTopEvent]"] = relationship("UserTopEvent", back_populates="event", cascade="all, delete-orphan")


class EventSet(Base):
    """
    EventSet model - many-to-many relationship between events and sets.
    
    Links sets to events. This is separate from recordings - sets can be
    linked to events without being recordings of those events.
    """
    __tablename__ = "event_sets"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    event_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    set_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dj_sets.id"), nullable=False, index=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    event: Mapped["Event"] = relationship("Event", foreign_keys=[event_id], back_populates="linked_sets")
    set: Mapped["DJSet"] = relationship("DJSet", foreign_keys=[set_id], back_populates="event_sets")
    
    # Unique constraint: prevent duplicate links
    __table_args__ = (
        UniqueConstraint('event_id', 'set_id', name='uq_event_set'),
    )


class EventConfirmation(Base):
    """
    Event Confirmation model - tracks which users confirmed a live event.
    
    Users can confirm that they attended a live event, which helps verify
    that the event actually happened. After a threshold of confirmations,
    the event can be auto-verified.
    """
    __tablename__ = "event_confirmations"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="event_confirmations")
    event: Mapped["Event"] = relationship("Event", back_populates="confirmations")
    
    # Unique constraint: user can only confirm an event once
    __table_args__ = (
        UniqueConstraint('user_id', 'event_id', name='uq_user_event_confirmation'),
    )
