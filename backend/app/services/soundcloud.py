"""
SoundCloud API integration service.

Handles fetching track information from SoundCloud using both oEmbed API
and the full SoundCloud API v2 (when credentials are available).
"""

import re
import httpx
from typing import Optional, Dict
from app.config import settings


def extract_track_id(url: str) -> Optional[str]:
    """
    Extract SoundCloud track ID or permalink from URL.
    
    Supports:
    - https://soundcloud.com/user/track-name
    - https://soundcloud.com/user/track-name?si=...
    """
    # SoundCloud URLs are typically: soundcloud.com/user/track-name
    # We'll use the full URL as the identifier
    pattern = r'soundcloud\.com/([^/]+)/([^/?]+)'
    match = re.search(pattern, url)
    
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    
    return None


async def fetch_soundcloud_track_info_api(url: str) -> Optional[Dict]:
    """
    Fetch track information using SoundCloud API v2 (full API).
    
    This provides more information including publish date and duration.
    
    Args:
        url: SoundCloud track URL
        
    Returns:
        Dictionary with track information, or None if API not available
    """
    client_id = settings.SOUNDCLOUD_CLIENT_ID
    
    if not client_id:
        # No API credentials, fall back to oEmbed
        return None
    
    # Use resolve endpoint to get track info
    resolve_url = "https://api.soundcloud.com/resolve"
    params = {
        "url": url,
        "client_id": client_id
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                resolve_url,
                params=params,
                timeout=30.0,
                follow_redirects=True
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract information from API response
            title = data.get("title", "")
            description = data.get("description", "")
            thumbnail_url = data.get("artwork_url") or data.get("user", {}).get("avatar_url")
            
            # Get user/DJ name
            user = data.get("user", {})
            dj_name = user.get("full_name") or user.get("username", "Unknown Artist")
            
            # Get duration (in milliseconds, convert to minutes)
            duration_ms = data.get("duration", 0)
            duration_minutes = int(duration_ms / 1000 / 60) if duration_ms else None
            
            # Get publish date
            created_at = data.get("created_at")
            
            return {
                "title": title,
                "description": description,
                "thumbnail_url": thumbnail_url,
                "dj_name": dj_name,
                "duration_minutes": duration_minutes,
                "created_at": created_at,  # Original publish date
                "metadata": {
                    "track_id": data.get("id"),
                    "permalink": data.get("permalink_url"),
                    "genre": data.get("genre"),
                    "tag_list": data.get("tag_list"),
                    "playback_count": data.get("playback_count"),
                    "likes_count": data.get("likes_count"),
                    "user_id": user.get("id"),
                    "user_username": user.get("username"),
                }
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Invalid client_id, fall back to oEmbed
                return None
            elif e.response.status_code == 404:
                raise Exception(f"SoundCloud track not found: {url}")
            # For other errors, fall back to oEmbed
            return None
        except Exception:
            # Any error, fall back to oEmbed
            return None


async def fetch_soundcloud_track_info(url: str) -> Dict:
    """
    Fetch track information from SoundCloud.
    
    Tries full API first (if credentials available), falls back to oEmbed.
    
    Args:
        url: SoundCloud track URL
        
    Returns:
        Dictionary with track information
        
    Raises:
        Exception: If API call fails or track not found
    """
    # Try full API first (if credentials available)
    api_info = await fetch_soundcloud_track_info_api(url)
    if api_info:
        return api_info
    
    # Fall back to oEmbed API
    oembed_url = "https://soundcloud.com/oembed"
    params = {
        "url": url,
        "format": "json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                oembed_url, 
                params=params, 
                timeout=30.0,
                follow_redirects=True
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract information from oEmbed response
            title = data.get("title", "")
            description = data.get("description", "")
            thumbnail_url = data.get("thumbnail_url")
            
            # Parse HTML to extract more info if needed
            html = data.get("html", "")
            
            # Extract user (DJ) name from title or description
            # SoundCloud titles are often "Track Name by Artist Name"
            dj_name = "Unknown Artist"
            if " by " in title:
                parts = title.split(" by ")
                if len(parts) > 1:
                    dj_name = parts[-1].strip()
            elif description:
                # Try to extract from description
                by_match = re.search(r'by\s+([^\n]+)', description, re.IGNORECASE)
                if by_match:
                    dj_name = by_match.group(1).strip()
            
            # Duration is not available in oEmbed, would need full API
            # For now, we'll leave it as None
            
            return {
                "title": title,
                "description": description,
                "thumbnail_url": thumbnail_url,
                "dj_name": dj_name,
                "duration_minutes": None,  # Not available via oEmbed
                "created_at": None,  # Not available via oEmbed
                "metadata": {
                    "author_name": data.get("author_name"),
                    "provider_name": "SoundCloud",
                    "html": html,
                    "source": "oembed"  # Indicate we used oEmbed
                }
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise Exception(f"SoundCloud track not found. Please check the URL: {url}")
            elif e.response.status_code >= 500:
                raise Exception(f"SoundCloud service is temporarily unavailable. Please try again later.")
            raise Exception(f"SoundCloud API error (status {e.response.status_code}): {str(e)}")
        except httpx.TimeoutException:
            raise Exception(f"Request to SoundCloud timed out. Please try again.")
        except httpx.RequestError as e:
            raise Exception(f"Failed to connect to SoundCloud: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to fetch SoundCloud track: {str(e)}")


async def import_from_soundcloud_url(url: str) -> Dict:
    """
    Import DJ set information from SoundCloud URL.
    
    Args:
        url: SoundCloud track URL
        
    Returns:
        Dictionary with set information ready for database
        
    Raises:
        Exception: If URL is invalid or API call fails
    """
    track_id = extract_track_id(url)
    
    if not track_id:
        raise Exception("Invalid SoundCloud URL format")
    
    track_info = await fetch_soundcloud_track_info(url)
    
    # Build metadata with publish date if available
    metadata = track_info.get("metadata", {})
    if track_info.get("created_at"):
        metadata["published_at"] = track_info["created_at"]
    
    return {
        "title": track_info["title"],
        "dj_name": track_info["dj_name"],
        "source_type": "soundcloud",
        "source_id": track_id,
        "source_url": url,
        "description": track_info["description"],
        "thumbnail_url": track_info["thumbnail_url"],
        "duration_minutes": track_info.get("duration_minutes"),
        "metadata": metadata
    }

