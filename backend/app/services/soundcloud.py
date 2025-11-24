"""
SoundCloud API integration service.

Handles fetching track information from SoundCloud using oEmbed API.
"""

import re
import httpx
from typing import Optional, Dict


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


async def fetch_soundcloud_track_info(url: str) -> Dict:
    """
    Fetch track information from SoundCloud oEmbed API.
    
    Args:
        url: SoundCloud track URL
        
    Returns:
        Dictionary with track information
        
    Raises:
        Exception: If API call fails or track not found
    """
    oembed_url = "https://soundcloud.com/oembed"
    params = {
        "url": url,
        "format": "json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(oembed_url, params=params, timeout=10.0)
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
                "metadata": {
                    "author_name": data.get("author_name"),
                    "provider_name": "SoundCloud",
                    "html": html
                }
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise Exception(f"SoundCloud track not found: {url}")
            raise Exception(f"SoundCloud API error: {str(e)}")
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
    
    return {
        "title": track_info["title"],
        "dj_name": track_info["dj_name"],
        "source_type": "soundcloud",
        "source_id": track_id,
        "source_url": url,
        "description": track_info["description"],
        "thumbnail_url": track_info["thumbnail_url"],
        "duration_minutes": track_info["duration_minutes"],
        "metadata": track_info["metadata"]
    }

