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


def _parse_spotify_tracks(data: dict) -> List[Dict]:
    """Parse Spotify search response into our standard track format."""
    tracks = data.get("tracks", {}).get("items", [])
    
    results = []
    for track in tracks:
        artists = track.get("artists", [])
        artist_names = ", ".join([artist.get("name", "") for artist in artists])
        
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
        
        artist_ids = [a.get("id") for a in artists if a.get("id")]
        results.append({
            "id": track.get("id"),
            "title": track.get("name", ""),
            "artist_name": artist_names,
            "artist_ids": artist_ids,
            "spotify_url": spotify_url,
            "thumbnail_url": thumbnail_url,
            "duration_ms": track.get("duration_ms", 0),
            "album_name": album.get("name", ""),
            "preview_url": track.get("preview_url"),
            "popularity": track.get("popularity", 0)
        })
    
    return results


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
    global _spotify_token_cache
    
    access_token = await get_spotify_access_token()
    if not access_token:
        logger.warning("No Spotify access token available for search")
        return []
    
    search_url = "https://api.spotify.com/v1/search"
    safe_limit = max(1, min(int(limit), 50))
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Build multiple param variants to try (Spotify API can be finicky)
    param_variants = [
        # Attempt 1: standard with limit as string and market
        {"q": query, "type": "track", "limit": str(safe_limit), "market": "US"},
        # Attempt 2: without market, limit as string
        {"q": query, "type": "track", "limit": str(safe_limit)},
        # Attempt 3: no limit at all (Spotify defaults to 20)
        {"q": query, "type": "track"},
    ]
    
    for i, params in enumerate(param_variants):
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Spotify search attempt {i+1} with params: {params}")
                response = await client.get(
                    search_url,
                    params=params,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return _parse_spotify_tracks(data)
                elif response.status_code == 401:
                    logger.warning("Spotify token expired, refreshing...")
                    _spotify_token_cache = None
                    access_token = await get_spotify_access_token()
                    if access_token:
                        headers = {"Authorization": f"Bearer {access_token}"}
                        retry_response = await client.get(
                            search_url,
                            params=params,
                            headers=headers,
                            timeout=10.0
                        )
                        if retry_response.status_code == 200:
                            return _parse_spotify_tracks(retry_response.json())
                    
                    logger.error(f"Spotify search failed after token refresh: {response.status_code}")
                else:
                    body = response.text[:300]
                    logger.warning(f"Spotify search attempt {i+1} failed: {response.status_code} - {body}")
                    
        except Exception as e:
            logger.warning(f"Spotify search attempt {i+1} exception: {str(e)}")
    
    logger.error("All Spotify search attempts failed")
    return []


def _format_track(track: Dict) -> Dict:
    """Normalize a Spotify track object into our standard format."""
    artists = track.get("artists", [])
    artist_names = ", ".join([a.get("name", "") for a in artists])
    
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
    
    # Extract artist IDs for recommendations
    artist_ids = [a.get("id") for a in artists if a.get("id")]
    
    return {
        "id": track.get("id"),
        "title": track.get("name", ""),
        "artist_name": artist_names,
        "artist_ids": artist_ids,
        "spotify_url": spotify_url,
        "thumbnail_url": thumbnail_url,
        "duration_ms": track.get("duration_ms", 0),
        "album_name": album.get("name", ""),
        "preview_url": track.get("preview_url"),
        "popularity": track.get("popularity", 0),
    }


async def get_genre_seeds() -> List[str]:
    """Get available genre seeds for recommendations."""
    access_token = await get_spotify_access_token()
    if not access_token:
        return []
    
    url = "https://api.spotify.com/v1/recommendations/available-genre-seeds"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return data.get("genres", [])
    except Exception as e:
        logger.error(f"Failed to get genre seeds: {str(e)}", exc_info=True)
        return []


async def get_recommendations(
    seed_tracks: Optional[List[str]] = None,
    seed_artists: Optional[List[str]] = None,
    seed_genres: Optional[List[str]] = None,
    limit: int = 20,
) -> List[Dict]:
    """
    Get track recommendations from Spotify.
    
    At least one seed (tracks, artists, or genres) is required.
    Combined seeds cannot exceed 5.
    """
    access_token = await get_spotify_access_token()
    if not access_token:
        return []
    
    url = "https://api.spotify.com/v1/recommendations"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    params: Dict = {"limit": min(limit, 100), "market": "US"}
    
    if seed_tracks:
        params["seed_tracks"] = ",".join(seed_tracks[:5])
    if seed_artists:
        params["seed_artists"] = ",".join(seed_artists[:5])
    if seed_genres:
        params["seed_genres"] = ",".join(seed_genres[:5])
    
    if not any(k.startswith("seed_") for k in params):
        logger.warning("No seeds provided for recommendations")
        return []
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return [_format_track(t) for t in data.get("tracks", [])]
    except Exception as e:
        logger.error(f"Failed to get recommendations: {str(e)}", exc_info=True)
        return []


async def get_new_releases(limit: int = 20, offset: int = 0) -> Dict:
    """
    Get new album releases, extract their tracks.
    
    Returns dict with 'albums' list and 'total' count.
    """
    access_token = await get_spotify_access_token()
    if not access_token:
        return {"albums": [], "total": 0}
    
    url = "https://api.spotify.com/v1/browse/new-releases"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"limit": min(limit, 50), "offset": offset, "country": "US"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            albums_data = data.get("albums", {})
            albums = []
            for album in albums_data.get("items", []):
                artists = album.get("artists", [])
                artist_names = ", ".join([a.get("name", "") for a in artists])
                images = album.get("images", [])
                thumbnail_url = None
                if images:
                    thumbnail_url = next(
                        (img.get("url") for img in images if img.get("height", 0) >= 300),
                        images[0].get("url") if images else None
                    )
                
                external_urls = album.get("external_urls", {})
                
                albums.append({
                    "id": album.get("id"),
                    "name": album.get("name", ""),
                    "artist_name": artist_names,
                    "thumbnail_url": thumbnail_url,
                    "release_date": album.get("release_date", ""),
                    "total_tracks": album.get("total_tracks", 0),
                    "album_type": album.get("album_type", ""),
                    "spotify_url": external_urls.get("spotify", ""),
                })
            
            return {
                "albums": albums,
                "total": albums_data.get("total", 0),
            }
    except Exception as e:
        logger.error(f"Failed to get new releases: {str(e)}", exc_info=True)
        return {"albums": [], "total": 0}


def _parse_artist(data: dict) -> Dict:
    """Parse a Spotify artist object into our standard format."""
    images = data.get("images", [])
    image_url = images[0]["url"] if images else None
    genres = data.get("genres", [])
    external_urls = data.get("external_urls", {})
    return {
        "spotify_artist_id": data.get("id"),
        "name": data.get("name", ""),
        "image_url": image_url,
        "genres": ", ".join(genres) if genres else None,
        "spotify_url": external_urls.get("spotify"),
        "followers": data.get("followers", {}).get("total", 0),
    }


async def get_artist(artist_id: str) -> Optional[Dict]:
    """Fetch an artist profile from Spotify."""
    global _spotify_token_cache
    access_token = await get_spotify_access_token()
    if not access_token:
        return None
    
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code in (401, 403):
                _spotify_token_cache = None
                access_token = await get_spotify_access_token()
                if access_token:
                    headers = {"Authorization": f"Bearer {access_token}"}
                    response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return _parse_artist(response.json())
    except Exception as e:
        logger.error(f"Failed to get artist {artist_id}: {str(e)}", exc_info=True)
        return None


async def get_artists_batch(artist_ids: List[str]) -> List[Dict]:
    """Fetch multiple artist profiles from Spotify. Falls back to individual fetches."""
    if not artist_ids:
        return []
    
    global _spotify_token_cache
    access_token = await get_spotify_access_token()
    if not access_token:
        return []
    
    url = "https://api.spotify.com/v1/artists"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"ids": ",".join(artist_ids[:50])}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            if response.status_code in (401, 403):
                _spotify_token_cache = None
                access_token = await get_spotify_access_token()
                if access_token:
                    headers = {"Authorization": f"Bearer {access_token}"}
                    response = await client.get(url, params=params, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return [_parse_artist(a) for a in data.get("artists", []) if a]
    except Exception as e:
        logger.warning(f"Batch artist fetch failed, falling back to individual: {e}")
        # Fallback: fetch one at a time
        results = []
        for aid in artist_ids:
            artist = await get_artist(aid)
            if artist:
                results.append(artist)
        return results


async def search_spotify_artist_by_name(name: str) -> Optional[Dict]:
    """Search Spotify for an artist by name. Returns the best match or None."""
    access_token = await get_spotify_access_token()
    if not access_token:
        return None

    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"q": name, "type": "artist", "limit": 5}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            artists = data.get("artists", {}).get("items", [])
            if not artists:
                return None
            # Prefer exact name match (case-insensitive), fall back to first result
            for artist in artists:
                if artist.get("name", "").lower() == name.lower():
                    return _parse_artist(artist)
            return _parse_artist(artists[0])
    except Exception as e:
        logger.warning(f"Spotify artist search failed for '{name}': {e}")
        return None


async def get_artist_top_tracks(artist_id: str) -> List[Dict]:
    """Get top tracks for a Spotify artist."""
    access_token = await get_spotify_access_token()
    if not access_token:
        return []
    
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"market": "US"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return [_format_track(t) for t in data.get("tracks", [])]
    except Exception as e:
        logger.error(f"Failed to get artist top tracks: {str(e)}", exc_info=True)
        return []


async def get_track_by_id(track_id: str) -> Optional[Dict]:
    """Get a single track by Spotify ID."""
    access_token = await get_spotify_access_token()
    if not access_token:
        return None
    
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return _format_track(response.json())
    except Exception as e:
        logger.error(f"Failed to get track by ID: {str(e)}", exc_info=True)
        return None


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
                "artist_ids": [a.get("id") for a in artists if a.get("id")],
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
