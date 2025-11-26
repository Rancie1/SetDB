"""
Database models (SQLAlchemy ORM).

This module defines all database tables as SQLAlchemy models.
Each model represents a table in the PostgreSQL database.
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import String, Text, Boolean, Integer, Float, Date, DateTime, ForeignKey, Enum, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
import enum


class SourceType(str, enum.Enum):
    """Enum for DJ set source types."""
    YOUTUBE = "youtube"
    SOUNDCLOUD = "soundcloud"
    LIVE = "live"


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
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile fields
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    # These allow us to access related data easily (e.g., user.reviews)
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    ratings: Mapped[List["Rating"]] = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    logs: Mapped[List["UserSetLog"]] = relationship("UserSetLog", back_populates="user", cascade="all, delete-orphan")
    created_sets: Mapped[List["DJSet"]] = relationship("DJSet", back_populates="created_by", foreign_keys="DJSet.created_by_id")
    lists: Mapped[List["List"]] = relationship("List", back_populates="user", cascade="all, delete-orphan")
    
    # Following relationships
    following: Mapped[List["Follow"]] = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan"
    )
    followers: Mapped[List["Follow"]] = relationship(
        "Follow",
        foreign_keys="Follow.following_id",
        back_populates="following",
        cascade="all, delete-orphan"
    )


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
    
    # Live event information (only for source_type='live')
    event_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    event_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    venue_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
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
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="set", cascade="all, delete-orphan")
    ratings: Mapped[List["Rating"]] = relationship("Rating", back_populates="set", cascade="all, delete-orphan")
    logs: Mapped[List["UserSetLog"]] = relationship("UserSetLog", back_populates="set", cascade="all, delete-orphan")
    list_items: Mapped[List["ListItem"]] = relationship("ListItem", back_populates="set", cascade="all, delete-orphan")
    
    # Unique constraint: prevent duplicate sets from same source
    __table_args__ = (
        UniqueConstraint('source_type', 'source_id', name='uq_set_source'),
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


class List(Base):
    """
    List model - user-created lists (e.g., "Best Techno Sets 2024").
    
    Users can create lists to organize sets. Lists can be public or private.
    """
    __tablename__ = "lists"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # List information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="lists")
    items: Mapped[List["ListItem"]] = relationship("ListItem", back_populates="list", cascade="all, delete-orphan", order_by="ListItem.position")


class ListItem(Base):
    """
    List Item model - sets included in lists.
    
    This is a many-to-many relationship between lists and sets.
    The position field allows ordered lists.
    """
    __tablename__ = "list_items"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    list_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lists.id"), nullable=False, index=True)
    set_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dj_sets.id"), nullable=False, index=True)
    
    # Item information
    position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    list: Mapped["List"] = relationship("List", back_populates="items")
    set: Mapped["DJSet"] = relationship("DJSet", back_populates="list_items")
    
    # Unique constraint: prevent duplicates in same list
    __table_args__ = (
        UniqueConstraint('list_id', 'set_id', name='uq_list_set_item'),
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


