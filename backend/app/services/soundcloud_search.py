"""
SoundCloud search service.

Provides functionality to search for tracks on SoundCloud.
"""

import httpx
import logging
from typing import Optional, List, Dict
from app.config import settings
from app.services.soundcloud import get_soundcloud_access_token

logger = logging.getLogger(__name__)


async def search_soundcloud_tracks(query: str, limit: int = 10) -> List[Dict]:
    """
    Search for tracks on SoundCloud.
    
    Args:
        query: Search query (track name, artist, etc.)
        limit: Maximum number of results to return (default: 10)
        
    Returns:
        List of track dictionaries with:
        - title: Track title
        - user: Artist/user info
        - permalink_url: SoundCloud URL
        - artwork_url: Thumbnail URL
        - id: Track ID
    """
    access_token = await get_soundcloud_access_token()
    if not access_token:
        logger.warning("No SoundCloud access token available for search")
        return []
    
    search_url = "https://api.soundcloud.com/tracks"
    params = {
        "q": query,
        "limit": min(limit, 50),  # SoundCloud API limit
        "linked_partitioning": "1"
    }
    headers = {
        "Authorization": f"OAuth {access_token}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                search_url,
                params=params,
                headers=headers,
                timeout=10.0,
                follow_redirects=True
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle paginated response
            if isinstance(data, dict) and "collection" in data:
                tracks = data["collection"]
            elif isinstance(data, list):
                tracks = data
            else:
                tracks = []
            
            # Format results
            results = []
            for track in tracks:
                user = track.get("user", {})
                results.append({
                    "id": track.get("id"),
                    "title": track.get("title", ""),
                    "artist_name": user.get("username", ""),
                    "soundcloud_url": track.get("permalink_url") or track.get("uri", ""),
                    "thumbnail_url": track.get("artwork_url") or user.get("avatar_url"),
                    "duration_ms": track.get("duration", 0),
                    "playback_count": track.get("playback_count", 0),
                    "likes_count": track.get("likes_count", 0)
                })
            
            return results
            
    except httpx.HTTPStatusError as e:
        logger.error(f"SoundCloud search API error: {e.response.status_code} - {e.response.text[:200]}")
        return []
    except Exception as e:
        logger.error(f"Failed to search SoundCloud: {str(e)}")
        return []


async def resolve_soundcloud_url(url: str) -> Optional[Dict]:
    """
    Resolve a SoundCloud URL to get track information.
    
    Args:
        url: SoundCloud track URL
        
    Returns:
        Track dictionary with track information, or None if not found
    """
    access_token = await get_soundcloud_access_token()
    if not access_token:
        return None
    
    resolve_url = "https://api.soundcloud.com/resolve"
    params = {"url": url}
    headers = {"Authorization": f"OAuth {access_token}"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                resolve_url,
                params=params,
                headers=headers,
                timeout=10.0,
                follow_redirects=True
            )
            response.raise_for_status()
            
            track = response.json()
            user = track.get("user", {})
            
            return {
                "id": track.get("id"),
                "title": track.get("title", ""),
                "artist_name": user.get("username", ""),
                "soundcloud_url": track.get("permalink_url") or track.get("uri", ""),
                "thumbnail_url": track.get("artwork_url") or user.get("avatar_url"),
                "duration_ms": track.get("duration", 0)
            }
            
    except Exception as e:
        logger.error(f"Failed to resolve SoundCloud URL: {str(e)}")
        return None
