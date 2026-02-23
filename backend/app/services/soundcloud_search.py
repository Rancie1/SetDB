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
            
            # Format results, filtering out long-form content (likely sets/mixes)
            results = []
            for track in tracks:
                duration_ms = track.get("duration", 0)
                # Skip content longer than 15 minutes (likely a DJ set, not a track)
                if duration_ms > 900000:
                    continue
                user = track.get("user", {})
                results.append({
                    "id": track.get("id"),
                    "title": track.get("title", ""),
                    "artist_name": user.get("username", ""),
                    "soundcloud_url": track.get("permalink_url") or track.get("uri", ""),
                    "thumbnail_url": track.get("artwork_url") or user.get("avatar_url"),
                    "duration_ms": duration_ms,
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


async def search_soundcloud_sets(query: str, limit: int = 10) -> List[Dict]:
    """
    Search for playlists/sets on SoundCloud (NOT tracks).
    
    The SoundCloud /playlists endpoint returns mixes, DJ sets, and playlists.
    We also search /tracks but filter for long-form content (> 10 min)
    which is more likely to be a DJ set/mix.
    """
    access_token = await get_soundcloud_access_token()
    if not access_token:
        logger.warning("No SoundCloud access token available for set search")
        return []
    
    headers = {"Authorization": f"OAuth {access_token}"}
    results = []
    
    try:
        async with httpx.AsyncClient() as client:
            # Search long tracks (> 10 minutes) which are likely mixes/sets
            track_params = {
                "q": query,
                "limit": min(limit, 50),
                "linked_partitioning": "1",
                "duration[from]": 600000,  # > 10 minutes in ms
            }
            response = await client.get(
                "https://api.soundcloud.com/tracks",
                params=track_params,
                headers=headers,
                timeout=10.0,
                follow_redirects=True,
            )
            response.raise_for_status()
            
            data = response.json()
            tracks = data.get("collection", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            
            for item in tracks:
                user = item.get("user", {})
                kind = item.get("kind", "track")
                # Skip podcasts/episodes
                if kind in ("podcast", "episode"):
                    continue
                results.append({
                    "id": item.get("id"),
                    "title": item.get("title", ""),
                    "dj_name": user.get("username", ""),
                    "soundcloud_url": item.get("permalink_url") or item.get("uri", ""),
                    "thumbnail_url": item.get("artwork_url") or user.get("avatar_url"),
                    "duration_ms": item.get("duration", 0),
                    "playback_count": item.get("playback_count", 0),
                    "likes_count": item.get("likes_count", 0),
                    "kind": kind,
                })
    except httpx.HTTPStatusError as e:
        logger.error(f"SoundCloud set search API error: {e.response.status_code} - {e.response.text[:200]}")
    except Exception as e:
        logger.error(f"Failed to search SoundCloud sets: {str(e)}")
    
    return results


async def resolve_soundcloud_url(url: str) -> Optional[Dict]:
    """
    Resolve a SoundCloud URL to get resource information.
    
    Returns a dict with a 'kind' field ('track', 'playlist', 'user', etc.)
    so callers can determine the content type.
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
            
            resource = response.json()
            user = resource.get("user", {})
            kind = resource.get("kind", "unknown")
            
            return {
                "id": resource.get("id"),
                "title": resource.get("title", ""),
                "artist_name": user.get("username", ""),
                "soundcloud_url": resource.get("permalink_url") or resource.get("uri", ""),
                "thumbnail_url": resource.get("artwork_url") or user.get("avatar_url"),
                "duration_ms": resource.get("duration", 0),
                "kind": kind,
            }
            
    except Exception as e:
        logger.error(f"Failed to resolve SoundCloud URL: {str(e)}")
        return None
