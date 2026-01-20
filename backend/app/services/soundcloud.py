"""
SoundCloud API integration service.

Handles fetching track information from SoundCloud using both oEmbed API
and the full SoundCloud API v2 (when credentials are available).
"""

import re
import httpx
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)

# Cache for access token (token, expires_at)
_token_cache: Optional[tuple[str, datetime]] = None


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


async def get_soundcloud_access_token() -> Optional[str]:
    """
    Get OAuth2 access token using client credentials flow.
    
    This token is cached and reused until it expires.
    
    Returns:
        Access token string, or None if authentication fails
    """
    global _token_cache
    
    client_id = settings.SOUNDCLOUD_CLIENT_ID
    client_secret = settings.SOUNDCLOUD_CLIENT_SECRET
    
    if not client_id or not client_secret:
        logger.warning("SoundCloud Client ID or Secret not configured")
        return None
    
    # Check if we have a valid cached token
    if _token_cache:
        token, expires_at = _token_cache
        if datetime.now() < expires_at - timedelta(seconds=60):  # Refresh 1 min before expiry
            return token
    
    # Get new token
    token_url = "https://api.soundcloud.com/oauth2/token"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)  # Default to 1 hour
                
                if access_token:
                    # Cache the token
                    expires_at = datetime.now() + timedelta(seconds=expires_in)
                    _token_cache = (access_token, expires_at)
                    logger.info(f"Obtained SoundCloud access token (expires in {expires_in}s)")
                    return access_token
            else:
                error_msg = f"Failed to get access token: {response.status_code} - {response.text[:200]}"
                logger.error(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"Error getting SoundCloud access token: {str(e)}"
            logger.error(error_msg, exc_info=True)
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
    client_secret = settings.SOUNDCLOUD_CLIENT_SECRET
    
    if not client_id or not client_secret:
        logger.info("SoundCloud credentials not configured, will use oEmbed API")
        return None
    
    # Get OAuth2 access token
    access_token = await get_soundcloud_access_token()
    if not access_token:
        logger.warning("Failed to get SoundCloud access token, falling back to oEmbed")
        return None
    
    logger.info("Using SoundCloud API v2 with OAuth2 authentication")
    
    # Use resolve endpoint to get track info
    resolve_url = "https://api.soundcloud.com/resolve"
    params = {
        "url": url
    }
    headers = {
        "Authorization": f"OAuth {access_token}"
    }
    
    logger.debug(f"Attempting SoundCloud API resolve for: {url}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                resolve_url,
                params=params,
                headers=headers,
                timeout=30.0,
                follow_redirects=True
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Log the full response to debug image URL issues
            logger.debug(f"SoundCloud API response keys: {list(data.keys())}")
            if "artwork_url" in data:
                logger.debug(f"artwork_url from API: {data.get('artwork_url')}")
            
            # Extract information from API response
            title = data.get("title", "")
            description = data.get("description", "")
            
            # Get user/DJ name first (needed to clean title)
            user = data.get("user", {})
            dj_name = user.get("full_name") or user.get("username", "Unknown Artist")
            
            # Remove " by Artist Name" from title if present
            # SoundCloud titles often include "Track Name by Artist Name"
            if " by " in title:
                # Split on " by " and take the first part (the track name)
                parts = title.split(" by ", 1)
                if len(parts) > 1:
                    title = parts[0].strip()
            
            # Get thumbnail URL from oEmbed for better quality (oEmbed returns higher quality images)
            # We'll use API for metadata but oEmbed for thumbnail
            thumbnail_url = None
            try:
                oembed_url = "https://soundcloud.com/oembed"
                oembed_params = {"url": url, "format": "json"}
                async with httpx.AsyncClient() as oembed_client:
                    oembed_response = await oembed_client.get(
                        oembed_url,
                        params=oembed_params,
                        timeout=10.0,
                        follow_redirects=True
                    )
                    if oembed_response.status_code == 200:
                        oembed_data = oembed_response.json()
                        thumbnail_url = oembed_data.get("thumbnail_url")
                        if thumbnail_url:
                            logger.debug(f"Using oEmbed thumbnail_url: {thumbnail_url}")
            except Exception as e:
                logger.warning(f"Failed to fetch oEmbed thumbnail, falling back to API artwork: {str(e)}")
            
            # Fallback to API artwork URL if oEmbed failed
            if not thumbnail_url:
                artwork_url = (
                    data.get("artwork_url") or 
                    data.get("artwork_url_large") or
                    data.get("artwork_url_original") or
                    data.get("user", {}).get("avatar_url")
                )
                if artwork_url:
                    logger.debug(f"Using API artwork_url: {artwork_url}")
                    # Try to get best quality version
                    if '-original.' in artwork_url:
                        thumbnail_url = artwork_url
                    elif '-large.' in artwork_url:
                        thumbnail_url = re.sub(r'-large\.(jpg|png)$', r'-original.\1', artwork_url)
                    else:
                        thumbnail_url = re.sub(r'-[a-z]\d+x\d+\.(jpg|png)$', r'-original.\1', artwork_url)
                        if thumbnail_url == artwork_url:
                            thumbnail_url = re.sub(r'\.(jpg|png)$', r'-original.\1', artwork_url)
            
            # Get duration (in milliseconds, convert to minutes)
            duration_ms = data.get("duration", 0)
            duration_minutes = int(duration_ms / 1000 / 60) if duration_ms else None
            
            # Get publish date
            created_at = data.get("created_at")
            
            logger.info(f"Successfully fetched track info using SoundCloud API v2 for: {title}")
            
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
                    "source": "api"  # Indicate we used full API
                }
            }
            
        except httpx.HTTPStatusError as e:
            error_msg = f"SoundCloud API error: {e.response.status_code} - {e.response.text[:200]}"
            logger.error(error_msg)
            
            if e.response.status_code == 401:
                # Token might be expired, try refreshing it once
                logger.warning("401 Unauthorized - token may be expired, clearing cache")
                global _token_cache
                _token_cache = None
                
                # Try once more with a fresh token
                access_token = await get_soundcloud_access_token()
                if access_token:
                    logger.info("Retrying with fresh token")
                    try:
                        response = await client.get(
                            resolve_url,
                            params=params,
                            headers={"Authorization": f"OAuth {access_token}"},
                            timeout=30.0,
                            follow_redirects=True
                        )
                        if response.status_code == 200:
                            # Success on retry, continue with normal flow
                            data = response.json()
                            # Extract and return data (same as below)
                            title = data.get("title", "")
                            description = data.get("description", "")
                            
                            # Get user/DJ name first (needed to clean title)
                            user = data.get("user", {})
                            dj_name = user.get("full_name") or user.get("username", "Unknown Artist")
                            
                            # Remove " by Artist Name" from title if present
                            if " by " in title:
                                parts = title.split(" by ", 1)
                                if len(parts) > 1:
                                    title = parts[0].strip()
                            
                            # Get thumbnail URL from oEmbed for better quality
                            thumbnail_url = None
                            try:
                                oembed_url = "https://soundcloud.com/oembed"
                                oembed_params = {"url": url, "format": "json"}
                                async with httpx.AsyncClient() as oembed_client:
                                    oembed_response = await oembed_client.get(
                                        oembed_url,
                                        params=oembed_params,
                                        timeout=10.0,
                                        follow_redirects=True
                                    )
                                    if oembed_response.status_code == 200:
                                        oembed_data = oembed_response.json()
                                        thumbnail_url = oembed_data.get("thumbnail_url")
                            except Exception:
                                pass  # Fall through to API artwork
                            
                            # Fallback to API artwork URL if oEmbed failed
                            if not thumbnail_url:
                                artwork_url = data.get("artwork_url") or data.get("user", {}).get("avatar_url")
                                if artwork_url:
                                    if '-original.' in artwork_url:
                                        thumbnail_url = artwork_url
                                    elif '-large.' in artwork_url:
                                        thumbnail_url = re.sub(r'-large\.(jpg|png)$', r'-original.\1', artwork_url)
                                    else:
                                        thumbnail_url = re.sub(r'-[a-z]\d+x\d+\.(jpg|png)$', r'-original.\1', artwork_url)
                                        if thumbnail_url == artwork_url:
                                            thumbnail_url = re.sub(r'\.(jpg|png)$', r'-original.\1', artwork_url)
                            duration_ms = data.get("duration", 0)
                            duration_minutes = int(duration_ms / 1000 / 60) if duration_ms else None
                            created_at = data.get("created_at")
                            
                            logger.info(f"Successfully fetched track info using SoundCloud API v2 for: {title}")
                            
                            return {
                                "title": title,
                                "description": description,
                                "thumbnail_url": thumbnail_url,
                                "dj_name": dj_name,
                                "duration_minutes": duration_minutes,
                                "created_at": created_at,
                                "metadata": {
                                    "track_id": data.get("id"),
                                    "permalink": data.get("permalink_url"),
                                    "genre": data.get("genre"),
                                    "tag_list": data.get("tag_list"),
                                    "playback_count": data.get("playback_count"),
                                    "likes_count": data.get("likes_count"),
                                    "user_id": user.get("id"),
                                    "user_username": user.get("username"),
                                    "source": "api"
                                }
                            }
                    except Exception:
                        pass  # Fall through to return None
                
                # If retry failed or credentials are invalid, fall back to oEmbed
                logger.warning("Authentication failed, falling back to oEmbed")
                return None
            elif e.response.status_code == 404:
                raise Exception(f"SoundCloud track not found: {url}")
            # For other errors, fall back to oEmbed
            logger.warning(f"HTTP error {e.response.status_code}, falling back to oEmbed")
            return None
        except httpx.RequestError as e:
            error_msg = f"SoundCloud API request error: {str(e)}"
            logger.error(error_msg)
            logger.warning("Network/request error, falling back to oEmbed")
            return None
        except Exception as e:
            # Any error, fall back to oEmbed
            error_msg = f"SoundCloud API unexpected error: {type(e).__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            logger.warning("Unexpected error, falling back to oEmbed")
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
        logger.info("Successfully fetched track info using SoundCloud API v2")
        return api_info
    
    # Fall back to oEmbed API
    logger.info("Falling back to SoundCloud oEmbed API (limited metadata)")
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
            
            # Use oEmbed thumbnail as-is (oEmbed returns good quality, don't modify)
            # oEmbed thumbnails are already optimized and high quality
            if thumbnail_url:
                logger.debug(f"oEmbed thumbnail (using as-is): {thumbnail_url}")
            
            # Parse HTML to extract more info if needed
            html = data.get("html", "")
            
            # Extract user (DJ) name from title or description
            # SoundCloud titles are often "Track Name by Artist Name"
            dj_name = "Unknown Artist"
            if " by " in title:
                parts = title.split(" by ", 1)
                if len(parts) > 1:
                    dj_name = parts[-1].strip()
                    # Remove " by Artist Name" from title
                    title = parts[0].strip()
            elif description:
                # Try to extract from description
                by_match = re.search(r'by\s+([^\n]+)', description, re.IGNORECASE)
                if by_match:
                    dj_name = by_match.group(1).strip()
            
            # Duration is not available in oEmbed, would need full API
            # For now, we'll leave it as None
            
            result = {
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
            logger.info("Successfully fetched track info using SoundCloud oEmbed API")
            return result
            
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
    
    Uses the full API for all metadata (duration, published_at, etc.)
    but uses oEmbed for the thumbnail (higher quality).
    
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
    
    # Always try to use the full API first (uses API for metadata, oEmbed for thumbnail)
    track_info = await fetch_soundcloud_track_info_api(url)
    
    # If API fails, fall back to oEmbed-only (limited metadata)
    if not track_info:
        logger.warning("API unavailable, falling back to oEmbed-only import")
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
        "thumbnail_url": track_info["thumbnail_url"],  # This comes from oEmbed when using API
        "duration_minutes": track_info.get("duration_minutes"),
        "metadata": metadata
    }

