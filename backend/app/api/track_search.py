"""
Track search API routes.

Handles searching for tracks on SoundCloud and creating tracks from search results.
"""

from fastapi import APIRouter, Depends, Query, Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models import Track, User
from app.schemas import TrackCreate, TrackResponse
from app.services import soundcloud_search
from app.services import spotify_search
from app.auth import get_current_active_user

router = APIRouter(prefix="/api/tracks", tags=["tracks"])

security = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Optional dependency to get current user if authenticated."""
    if not credentials:
        return None
    try:
        from app.auth import oauth2_scheme
        from jose import JWTError, jwt
        from app.config import settings
        
        # Decode the token
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Extract user_id from token
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            return None
        
        # Fetch user from database
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        
        return user
    except:
        return None


@router.get("/search/soundcloud", response_model=List[dict])
async def search_soundcloud(
    query: str = Query(..., min_length=1, description="Search query for tracks"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Search for tracks on SoundCloud.
    
    This endpoint is publicly accessible (no authentication required).
    Returns track information including title, artist, SoundCloud URL, and metadata.
    Also checks if tracks already exist in the database.
    """
    results = await soundcloud_search.search_soundcloud_tracks(query, limit)
    
    # Check which tracks already exist in database
    if results:
        soundcloud_urls = [r.get('soundcloud_url') for r in results if r.get('soundcloud_url')]
        soundcloud_ids = [r.get('id') for r in results if r.get('id')]
        
        existing_tracks = []
        if soundcloud_urls:
            existing_by_url = await db.execute(
                select(Track).where(Track.soundcloud_url.in_(soundcloud_urls))
            )
            existing_tracks.extend(existing_by_url.scalars().all())
        
        if soundcloud_ids:
            existing_by_id = await db.execute(
                select(Track).where(Track.soundcloud_track_id.in_([str(sid) for sid in soundcloud_ids]))
            )
            existing_tracks.extend(existing_by_id.scalars().all())
        
        # Create a set of existing SoundCloud URLs and IDs
        existing_urls = {t.soundcloud_url for t in existing_tracks if t.soundcloud_url}
        existing_ids = {t.soundcloud_track_id for t in existing_tracks if t.soundcloud_track_id}
        
        # Add existence flag and platform to results
        for result in results:
            result['platform'] = 'soundcloud'
            result['exists_in_db'] = (
                result.get('soundcloud_url') in existing_urls or
                str(result.get('id')) in existing_ids
            )
            # If exists, add the track ID
            if result['exists_in_db']:
                for track in existing_tracks:
                    if (track.soundcloud_url == result.get('soundcloud_url') or
                        track.soundcloud_track_id == str(result.get('id'))):
                        result['track_id'] = str(track.id)
                        break
    
    return results


@router.get("/search/spotify", response_model=List[dict])
async def search_spotify(
    query: str = Query(..., min_length=1, description="Search query for tracks"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Search for tracks on Spotify.
    
    This endpoint is publicly accessible (no authentication required).
    Returns track information including title, artist, Spotify URL, and metadata.
    Also checks if tracks already exist in the database.
    """
    results = await spotify_search.search_spotify_tracks(query, limit)
    
    # Check which tracks already exist in database
    if results:
        spotify_urls = [r.get('spotify_url') for r in results if r.get('spotify_url')]
        spotify_ids = [r.get('id') for r in results if r.get('id')]
        
        existing_tracks = []
        if spotify_urls:
            existing_by_url = await db.execute(
                select(Track).where(Track.spotify_url.in_(spotify_urls))
            )
            existing_tracks.extend(existing_by_url.scalars().all())
        
        if spotify_ids:
            existing_by_id = await db.execute(
                select(Track).where(Track.spotify_track_id.in_(spotify_ids))
            )
            existing_tracks.extend(existing_by_id.scalars().all())
        
        # Create a set of existing Spotify URLs and IDs
        existing_urls = {t.spotify_url for t in existing_tracks if t.spotify_url}
        existing_ids = {t.spotify_track_id for t in existing_tracks if t.spotify_track_id}
        
        # Add existence flag and platform to results
        for result in results:
            result['platform'] = 'spotify'
            result['exists_in_db'] = (
                result.get('spotify_url') in existing_urls or
                result.get('id') in existing_ids
            )
            # If exists, add the track ID
            if result['exists_in_db']:
                for track in existing_tracks:
                    if (track.spotify_url == result.get('spotify_url') or
                        track.spotify_track_id == result.get('id')):
                        result['track_id'] = str(track.id)
                        break
    
    return results


@router.get("/search", response_model=List[dict])
async def search_tracks(
    query: str = Query(..., min_length=1, description="Search query for tracks"),
    platform: str = Query("all", pattern="^(all|soundcloud|spotify)$", description="Platform to search: all, soundcloud, or spotify"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results per platform"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Search for tracks across multiple platforms (SoundCloud and/or Spotify).
    
    This endpoint is publicly accessible (no authentication required).
    Returns combined results from selected platforms.
    """
    all_results = []
    
    if platform in ("all", "soundcloud"):
        soundcloud_results = await soundcloud_search.search_soundcloud_tracks(query, limit)
        for result in soundcloud_results:
            result['platform'] = 'soundcloud'
        all_results.extend(soundcloud_results)
    
    if platform in ("all", "spotify"):
        spotify_results = await spotify_search.search_spotify_tracks(query, limit)
        for result in spotify_results:
            result['platform'] = 'spotify'
        all_results.extend(spotify_results)
    
    # Check which tracks already exist in database
    if all_results:
        # Collect all URLs and IDs
        soundcloud_urls = [r.get('soundcloud_url') for r in all_results if r.get('soundcloud_url')]
        soundcloud_ids = [str(r.get('id')) for r in all_results if r.get('platform') == 'soundcloud' and r.get('id')]
        spotify_urls = [r.get('spotify_url') for r in all_results if r.get('spotify_url')]
        spotify_ids = [r.get('id') for r in all_results if r.get('platform') == 'spotify' and r.get('id')]
        
        existing_tracks = []
        if soundcloud_urls:
            existing_by_url = await db.execute(
                select(Track).where(Track.soundcloud_url.in_(soundcloud_urls))
            )
            existing_tracks.extend(existing_by_url.scalars().all())
        
        if soundcloud_ids:
            existing_by_id = await db.execute(
                select(Track).where(Track.soundcloud_track_id.in_(soundcloud_ids))
            )
            existing_tracks.extend(existing_by_id.scalars().all())
        
        if spotify_urls:
            existing_by_url = await db.execute(
                select(Track).where(Track.spotify_url.in_(spotify_urls))
            )
            existing_tracks.extend(existing_by_url.scalars().all())
        
        if spotify_ids:
            existing_by_id = await db.execute(
                select(Track).where(Track.spotify_track_id.in_(spotify_ids))
            )
            existing_tracks.extend(existing_by_id.scalars().all())
        
        # Create sets of existing URLs and IDs
        existing_soundcloud_urls = {t.soundcloud_url for t in existing_tracks if t.soundcloud_url}
        existing_soundcloud_ids = {t.soundcloud_track_id for t in existing_tracks if t.soundcloud_track_id}
        existing_spotify_urls = {t.spotify_url for t in existing_tracks if t.spotify_url}
        existing_spotify_ids = {t.spotify_track_id for t in existing_tracks if t.spotify_track_id}
        
        # Add existence flags to results
        for result in all_results:
            if result.get('platform') == 'soundcloud':
                result['exists_in_db'] = (
                    result.get('soundcloud_url') in existing_soundcloud_urls or
                    str(result.get('id')) in existing_soundcloud_ids
                )
                if result['exists_in_db']:
                    for track in existing_tracks:
                        if (track.soundcloud_url == result.get('soundcloud_url') or
                            track.soundcloud_track_id == str(result.get('id'))):
                            result['track_id'] = str(track.id)
                            break
            elif result.get('platform') == 'spotify':
                result['exists_in_db'] = (
                    result.get('spotify_url') in existing_spotify_urls or
                    result.get('id') in existing_spotify_ids
                )
                if result['exists_in_db']:
                    for track in existing_tracks:
                        if (track.spotify_url == result.get('spotify_url') or
                            track.spotify_track_id == result.get('id')):
                            result['track_id'] = str(track.id)
                            break
    
    return all_results


@router.get("/resolve-url", response_model=dict)
async def resolve_track_url(
    url: str = Query(..., description="SoundCloud or Spotify track URL to resolve"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Resolve a SoundCloud or Spotify URL to get track information.
    
    This endpoint is publicly accessible (no authentication required).
    Returns track information and checks if it already exists in the database.
    """
    is_soundcloud = 'soundcloud.com' in url
    is_spotify = 'spotify.com' in url or url.startswith('spotify:track:')
    
    if not is_soundcloud and not is_spotify:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL. Please provide a SoundCloud or Spotify track URL"
        )
    
    track_info = None
    
    if is_soundcloud:
        track_info = await soundcloud_search.resolve_soundcloud_url(url)
        if track_info:
            track_info['platform'] = 'soundcloud'
    elif is_spotify:
        track_info = await spotify_search.resolve_spotify_url(url)
        if track_info:
            track_info['platform'] = 'spotify'
    
    if not track_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not resolve track information from URL"
        )
    
    # Check if track already exists in database
    track_info['exists_in_db'] = False
    track_info['track_id'] = None
    
    if is_soundcloud:
        if track_info.get('soundcloud_url'):
            existing = await db.execute(
                select(Track).where(Track.soundcloud_url == track_info['soundcloud_url'])
            )
            existing_track = existing.scalar_one_or_none()
            if existing_track:
                track_info['exists_in_db'] = True
                track_info['track_id'] = str(existing_track.id)
        
        if not track_info['exists_in_db'] and track_info.get('id'):
            existing = await db.execute(
                select(Track).where(Track.soundcloud_track_id == str(track_info['id']))
            )
            existing_track = existing.scalar_one_or_none()
            if existing_track:
                track_info['exists_in_db'] = True
                track_info['track_id'] = str(existing_track.id)
    
    elif is_spotify:
        if track_info.get('spotify_url'):
            existing = await db.execute(
                select(Track).where(Track.spotify_url == track_info['spotify_url'])
            )
            existing_track = existing.scalar_one_or_none()
            if existing_track:
                track_info['exists_in_db'] = True
                track_info['track_id'] = str(existing_track.id)
        
        if not track_info['exists_in_db'] and track_info.get('id'):
            existing = await db.execute(
                select(Track).where(Track.spotify_track_id == track_info['id'])
            )
            existing_track = existing.scalar_one_or_none()
            if existing_track:
                track_info['exists_in_db'] = True
                track_info['track_id'] = str(existing_track.id)
    
    return track_info



