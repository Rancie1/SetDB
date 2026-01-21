"""
Spotify search service.

Provides functionality to search for tracks on Spotify.
"""

import httpx
import logging
import base64
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)

# Cache for access token (token, expires_at)
_spotify_token_cache: Optional[tuple[str, datetime]] = None


async def get_spotify_access_token() -> Optional[str]:
    """
    Get OAuth2 access token using client credentials flow.
    
    This token is cached and reused until it expires.
    
    Returns:
        Access token string, or None if authentication fails
    """
    global _spotify_token_cache
    
    client_id = settings.SPOTIFY_CLIENT_ID
    client_secret = settings.SPOTIFY_CLIENT_SECRET
    
    if not client_id or not client_secret:
        logger.warning("Spotify Client ID or Secret not configured")
        return None
    
    # Check if we have a valid cached token
    if _spotify_token_cache:
        token, expires_at = _spotify_token_cache
        if datetime.now() < expires_at - timedelta(seconds=60):  # Refresh 1 min before expiry
            return token
    
    # Get new token
    token_url = "https://accounts.spotify.com/api/token"
    
    # Spotify requires Basic Auth with base64 encoded client_id:client_secret
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "client_credentials"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                token_url,
                headers=headers,
                data=data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour
                
                if access_token:
                    # Cache the token
                    expires_at = datetime.now() + timedelta(seconds=expires_in)
                    _spotify_token_cache = (access_token, expires_at)
                    logger.info(f"Obtained Spotify access token (expires in {expires_in}s)")
                    return access_token
            else:
                error_msg = f"Failed to get Spotify access token: {response.status_code} - {response.text[:200]}"
                logger.error(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"Error getting Spotify access token: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None


async def search_spotify_tracks(query: str, limit: int = 10) -> List[Dict]:
    """
    Search for tracks on Spotify.
    
    Args:
        query: Search query (track name, artist, etc.)
        limit: Maximum number of results to return (default: 10, max: 50)
        
    Returns:
        List of track dictionaries with:
        - id: Spotify track ID
        - title: Track name
        - artist_name: Artist name(s)
        - spotify_url: Spotify track URL
        - thumbnail_url: Album artwork URL
        - duration_ms: Track duration in milliseconds
    """
    access_token = await get_spotify_access_token()
    if not access_token:
        logger.warning("No Spotify access token available for search")
        return []
    
    search_url = "https://api.spotify.com/v1/search"
    params = {
        "q": query,
        "type": "track",
        "limit": min(limit, 50),  # Spotify API limit
        "market": "US"  # Market code (can be made configurable)
    }
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                search_url,
                params=params,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            
            data = response.json()
            tracks = data.get("tracks", {}).get("items", [])
            
            # Format results
            results = []
            for track in tracks:
                # Get artist names (can be multiple)
                artists = track.get("artists", [])
                artist_names = ", ".join([artist.get("name", "") for artist in artists])
                
                # Get album artwork (prefer largest available)
                album = track.get("album", {})
                images = album.get("images", [])
                thumbnail_url = None
                if images:
                    # Prefer medium or large image
                    thumbnail_url = next(
                        (img.get("url") for img in images if img.get("height", 0) >= 300),
                        images[0].get("url") if images else None
                    )
                
                # Get external URLs
                external_urls = track.get("external_urls", {})
                spotify_url = external_urls.get("spotify", "")
                
                results.append({
                    "id": track.get("id"),
                    "title": track.get("name", ""),
                    "artist_name": artist_names,
                    "spotify_url": spotify_url,
                    "thumbnail_url": thumbnail_url,
                    "duration_ms": track.get("duration_ms", 0),
                    "album_name": album.get("name", ""),
                    "preview_url": track.get("preview_url"),  # 30-second preview
                    "popularity": track.get("popularity", 0)
                })
            
            return results
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Spotify search API error: {e.response.status_code} - {e.response.text[:200]}")
        return []
    except Exception as e:
        logger.error(f"Failed to search Spotify: {str(e)}", exc_info=True)
        return []


async def resolve_spotify_url(url: str) -> Optional[Dict]:
    """
    Resolve a Spotify URL to get track information.
    
    Args:
        url: Spotify track URL (e.g., https://open.spotify.com/track/...)
        
    Returns:
        Track dictionary with track information, or None if not found
    """
    access_token = await get_spotify_access_token()
    if not access_token:
        return None
    
    # Extract track ID from URL
    # Spotify URLs can be: https://open.spotify.com/track/{id} or spotify:track:{id}
    track_id = None
    if "spotify.com/track/" in url:
        track_id = url.split("spotify.com/track/")[-1].split("?")[0].split("/")[0]
    elif url.startswith("spotify:track:"):
        track_id = url.replace("spotify:track:", "")
    
    if not track_id:
        logger.warning(f"Could not extract track ID from Spotify URL: {url}")
        return None
    
    # Get track info from Spotify API
    track_url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                track_url,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            
            track = response.json()
            
            # Get artist names
            artists = track.get("artists", [])
            artist_names = ", ".join([artist.get("name", "") for artist in artists])
            
            # Get album artwork
            album = track.get("album", {})
            images = album.get("images", [])
            thumbnail_url = None
            if images:
                thumbnail_url = next(
                    (img.get("url") for img in images if img.get("height", 0) >= 300),
                    images[0].get("url") if images else None
                )
            
            external_urls = track.get("external_urls", {})
            spotify_url = external_urls.get("spotify", "")
            
            return {
                "id": track.get("id"),
                "title": track.get("name", ""),
                "artist_name": artist_names,
                "spotify_url": spotify_url,
                "thumbnail_url": thumbnail_url,
                "duration_ms": track.get("duration_ms", 0),
                "album_name": album.get("name", ""),
                "preview_url": track.get("preview_url"),
                "popularity": track.get("popularity", 0)
            }
            
    except Exception as e:
        logger.error(f"Failed to resolve Spotify URL: {str(e)}", exc_info=True)
        return None
