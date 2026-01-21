"""
Unified set importer service.

Provides a single interface for importing DJ sets from different platforms.
Automatically detects the platform from the URL and calls the appropriate service.
"""

import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models import DJSet, SourceType
from app.services.youtube import import_from_youtube_url
from app.services.soundcloud import import_from_soundcloud_url


def detect_platform(url: str) -> Optional[str]:
    """
    Detect the platform from a URL.
    
    Returns:
        'youtube', 'soundcloud', or None if unknown
    """
    url_lower = url.lower()
    
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    elif "soundcloud.com" in url_lower:
        return "soundcloud"
    
    return None


async def import_set(
    url: str,
    user_id: UUID,
    db: AsyncSession,
    source: Optional[str] = None
) -> DJSet:
    """
    Import a DJ set from an external URL.
    
    This is the main function that:
    1. Detects the platform from the URL (or uses provided source)
    2. Calls the appropriate service to fetch data
    3. Creates a DJSet record in the database
    4. Returns the created set
    
    Args:
        url: URL of the set (YouTube, SoundCloud, etc.)
        user_id: ID of the user importing the set
        db: Database session
        source: Optional platform override ('youtube' or 'soundcloud')
        
    Returns:
        Created DJSet object
        
    Raises:
        Exception: If platform is unsupported or import fails
    """
    # Detect platform if not provided
    if not source:
        source = detect_platform(url)
    
    if not source:
        raise Exception("Unsupported platform. Please provide a YouTube or SoundCloud URL.")
    
    # Check if set already exists
    if source == "youtube":
        from app.services.youtube import extract_video_id
        source_id = extract_video_id(url)
        source_type = SourceType.YOUTUBE
    elif source == "soundcloud":
        from app.services.soundcloud import extract_track_id
        source_id = extract_track_id(url)
        source_type = SourceType.SOUNDCLOUD
    else:
        raise Exception(f"Unsupported source: {source}")
    
    # Check for duplicates
    from sqlalchemy import select
    existing = await db.execute(
        select(DJSet).where(
            DJSet.source_type == source_type,
            DJSet.source_id == source_id
        )
    )
    if existing.scalar_one_or_none():
        raise Exception("This set has already been imported")
    
    # Import from the appropriate service
    if source == "youtube":
        set_data = await import_from_youtube_url(url)
    elif source == "soundcloud":
        set_data = await import_from_soundcloud_url(url)
    else:
        raise Exception(f"Unsupported source: {source}")
    
    # Create DJSet object
    new_set = DJSet(
        title=set_data["title"],
        dj_name=set_data["dj_name"],
        source_type=source_type,
        source_id=source_id,
        source_url=url,
        description=set_data.get("description"),
        thumbnail_url=set_data.get("thumbnail_url"),
        duration_minutes=set_data.get("duration_minutes"),
        extra_metadata=set_data.get("metadata"),
        created_by_id=user_id
    )
    
    db.add(new_set)
    await db.commit()
    await db.refresh(new_set)
    
    return new_set


async def import_set_as_live(
    url: str,
    user_id: UUID,
    db: AsyncSession,
    source: Optional[str] = None
) -> DJSet:
    """
    Import a DJ set from an external URL and create it as a live set.
    
    The imported URL is stored as recording_url, and the set is created
    as source_type='live' so it appears on the discover page as a live set.
    
    Args:
        url: URL of the set (YouTube, SoundCloud, etc.)
        user_id: ID of the user importing the set
        db: Database session
        source: Optional platform override ('youtube' or 'soundcloud')
        
    Returns:
        Created DJSet object (as live set)
        
    Raises:
        Exception: If platform is unsupported or import fails
    """
    # Detect platform if not provided
    if not source:
        source = detect_platform(url)
    
    if not source:
        raise Exception("Unsupported platform. Please provide a YouTube or SoundCloud URL.")
    
    # Import from the appropriate service to get metadata
    if source == "youtube":
        set_data = await import_from_youtube_url(url)
    elif source == "soundcloud":
        set_data = await import_from_soundcloud_url(url)
    else:
        raise Exception(f"Unsupported source: {source}")
    
    # Generate unique source_url for live set
    # Clean the title and dj_name to avoid special characters that might cause issues
    from uuid import uuid4
    import re
    clean_dj_name = re.sub(r'[^\w\s-]', '', set_data.get('dj_name', 'Unknown'))[:50]
    clean_title = re.sub(r'[^\w\s-]', '', set_data.get('title', 'Untitled'))[:50]
    unique_id = str(uuid4())[:8]
    live_source_url = f"live://{clean_dj_name}-{clean_title}-{unique_id}"
    
    # Ensure uniqueness by checking if this source_url already exists
    from sqlalchemy import select
    existing_check = await db.execute(
        select(DJSet).where(DJSet.source_url == live_source_url)
    )
    if existing_check.scalar_one_or_none():
        # If somehow duplicate, add more randomness
        unique_id = str(uuid4())
        live_source_url = f"live://{clean_dj_name}-{clean_title}-{unique_id}"
    
    # Create live set with recording URL (NOT an event)
    new_set = DJSet(
        title=set_data["title"],
        dj_name=set_data["dj_name"],
        source_type=SourceType.LIVE,
        source_id=None,  # Live sets don't have source_id
        source_url=live_source_url,
        description=set_data.get("description"),
        thumbnail_url=set_data.get("thumbnail_url"),
        duration_minutes=set_data.get("duration_minutes"),
        recording_url=url,  # Store the YouTube/SoundCloud URL as recording
        extra_metadata=set_data.get("metadata"),
        created_by_id=user_id
    )
    
    db.add(new_set)
    await db.commit()
    await db.refresh(new_set)
    
    return new_set

