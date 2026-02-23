"""
Spotify OAuth service.

Handles OAuth2 Authorization Code flow for user authentication via Spotify.
Follows the same patterns as Google/SoundCloud OAuth for consistency.
"""

import httpx
import logging
import base64
from typing import Optional, Dict
from app.config import settings

logger = logging.getLogger(__name__)


class SpotifyOAuthConfigurationError(Exception):
    """Raised when Spotify OAuth is not properly configured."""
    pass


class SpotifyOAuthAPIError(Exception):
    """Raised when Spotify OAuth API requests fail."""
    pass


def _get_client_credentials_header() -> str:
    """Encode client_id:client_secret as Base64 for Spotify's token endpoint."""
    credentials = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    return base64.b64encode(credentials.encode()).decode()


def _validate_config():
    """Validate Spotify OAuth configuration. Raises if not configured."""
    if not settings.is_spotify_oauth_configured():
        errors = []
        if not settings.SPOTIFY_CLIENT_ID:
            errors.append("SPOTIFY_CLIENT_ID is not set")
        if not settings.SPOTIFY_CLIENT_SECRET:
            errors.append("SPOTIFY_CLIENT_SECRET is not set")
        if not settings.SPOTIFY_REDIRECT_URI:
            errors.append("SPOTIFY_REDIRECT_URI is not set")
        raise SpotifyOAuthConfigurationError(
            "Spotify OAuth is not properly configured: " + "; ".join(errors)
        )


def get_spotify_oauth_url(state: str) -> str:
    """
    Generate Spotify OAuth authorization URL.
    
    Args:
        state: CSRF protection token
        
    Returns:
        URL to redirect user to for authorization
    """
    _validate_config()
    
    client_id = settings.SPOTIFY_CLIENT_ID
    redirect_uri = settings.SPOTIFY_REDIRECT_URI
    
    logger.info(f"Generating Spotify OAuth URL with redirect_uri: {redirect_uri}")
    
    auth_url = "https://accounts.spotify.com/authorize"
    
    from urllib.parse import urlencode
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": "user-read-email user-read-private",
        "state": state,
        "show_dialog": "true",
    }
    
    final_url = f"{auth_url}?{urlencode(params)}"
    logger.info(f"Generated Spotify authorization URL")
    
    return final_url


async def exchange_code_for_token(code: str) -> Optional[Dict]:
    """
    Exchange authorization code for access token.
    
    Spotify requires client credentials as a Base64 Authorization header.
    
    Args:
        code: Authorization code from Spotify callback
        
    Returns:
        Dictionary with access_token, refresh_token, expires_in, etc.
    """
    _validate_config()
    
    token_url = "https://accounts.spotify.com/api/token"
    auth_header = _get_client_credentials_header()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
                },
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=30.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Successfully exchanged Spotify code for token")
                return data
            else:
                error_text = response.text[:200]
                if "invalid_grant" in error_text.lower():
                    logger.warning(f"Spotify token exchange failed with invalid_grant: {error_text}")
                    raise SpotifyOAuthAPIError(
                        "Authorization code is invalid or has already been used. Please try signing in again."
                    )
                elif "invalid_client" in error_text.lower():
                    logger.error(f"Spotify token exchange failed with invalid_client: {error_text}")
                    raise SpotifyOAuthConfigurationError(
                        "Spotify OAuth client credentials are invalid. Please check your configuration."
                    )
                else:
                    logger.error(f"Spotify token exchange failed: {response.status_code} - {error_text}")
                    raise SpotifyOAuthAPIError(
                        f"Failed to exchange authorization code. Spotify returned: {error_text}"
                    )
                    
        except httpx.TimeoutException:
            logger.error("Spotify token exchange request timed out")
            raise SpotifyOAuthAPIError("Request to Spotify timed out. Please try again.")
        except httpx.NetworkError as e:
            logger.error(f"Network error during Spotify token exchange: {str(e)}")
            raise SpotifyOAuthAPIError(
                "Network error occurred while connecting to Spotify. Please check your internet connection."
            )
        except Exception as e:
            if isinstance(e, (SpotifyOAuthConfigurationError, SpotifyOAuthAPIError)):
                raise
            logger.error(f"Unexpected error exchanging Spotify code for token: {str(e)}", exc_info=True)
            raise SpotifyOAuthAPIError("An unexpected error occurred during authentication. Please try again.")


async def get_spotify_user_info(access_token: str) -> Optional[Dict]:
    """
    Get user information from Spotify API using access token.
    
    Args:
        access_token: OAuth access token
        
    Returns:
        Dictionary with user info (id, email, display_name, images, etc.)
    """
    api_url = "https://api.spotify.com/v1/me"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                api_url,
                headers=headers,
                timeout=30.0,
                follow_redirects=True,
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched Spotify user info: {data.get('display_name')}")
                return data
            elif response.status_code == 401:
                logger.error(f"Unauthorized access to Spotify user info: {response.text[:200]}")
                raise SpotifyOAuthAPIError("Access token is invalid or expired. Please sign in again.")
            else:
                error_text = response.text[:200]
                logger.error(f"Failed to get Spotify user info: {response.status_code} - {error_text}")
                raise SpotifyOAuthAPIError(
                    f"Failed to fetch user information from Spotify. Status: {response.status_code}"
                )
                
        except httpx.TimeoutException:
            logger.error("Spotify user info request timed out")
            raise SpotifyOAuthAPIError("Request to Spotify timed out. Please try again.")
        except httpx.NetworkError as e:
            logger.error(f"Network error during Spotify user info fetch: {str(e)}")
            raise SpotifyOAuthAPIError(
                "Network error occurred while fetching user information. Please check your internet connection."
            )
        except Exception as e:
            if isinstance(e, SpotifyOAuthAPIError):
                raise
            logger.error(f"Unexpected error getting Spotify user info: {str(e)}", exc_info=True)
            raise SpotifyOAuthAPIError("An unexpected error occurred while fetching user information. Please try again.")


async def refresh_spotify_token(refresh_token: str) -> Optional[Dict]:
    """
    Refresh an expired Spotify access token.
    
    Args:
        refresh_token: Refresh token from initial OAuth flow
        
    Returns:
        Dictionary with new access_token, expires_in, etc.
    """
    _validate_config()
    
    token_url = "https://accounts.spotify.com/api/token"
    auth_header = _get_client_credentials_header()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=30.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Successfully refreshed Spotify token")
                return data
            else:
                error_text = response.text[:200]
                logger.error(f"Spotify token refresh failed: {response.status_code} - {error_text}")
                raise SpotifyOAuthAPIError(
                    f"Failed to refresh access token. Spotify returned: {error_text}"
                )
                
        except httpx.TimeoutException:
            logger.error("Spotify token refresh request timed out")
            raise SpotifyOAuthAPIError("Request to Spotify timed out. Please try again.")
        except httpx.NetworkError as e:
            logger.error(f"Network error during Spotify token refresh: {str(e)}")
            raise SpotifyOAuthAPIError(
                "Network error occurred while refreshing token. Please check your internet connection."
            )
        except Exception as e:
            if isinstance(e, (SpotifyOAuthConfigurationError, SpotifyOAuthAPIError)):
                raise
            logger.error(f"Unexpected error refreshing Spotify token: {str(e)}", exc_info=True)
            raise SpotifyOAuthAPIError("An unexpected error occurred while refreshing token. Please try again.")
