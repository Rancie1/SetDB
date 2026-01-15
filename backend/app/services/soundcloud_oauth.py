"""
SoundCloud OAuth service.

Handles OAuth2 Authorization Code flow for user authentication.
This is different from the client credentials flow used for API access.
"""

import httpx
import logging
from typing import Optional, Dict
from app.config import settings

logger = logging.getLogger(__name__)


def get_soundcloud_oauth_url(state: str) -> str:
    """
    Generate SoundCloud OAuth authorization URL.
    
    Args:
        state: CSRF protection token (should be stored in session)
        
    Returns:
        URL to redirect user to for authorization
    """
    client_id = settings.SOUNDCLOUD_CLIENT_ID
    redirect_uri = settings.SOUNDCLOUD_REDIRECT_URI
    
    if not client_id or not redirect_uri:
        raise ValueError("SoundCloud OAuth not configured. Set SOUNDCLOUD_CLIENT_ID and SOUNDCLOUD_REDIRECT_URI")
    
    # Log configuration for debugging (don't log full client_id in production)
    logger.info(f"Generating SoundCloud OAuth URL with redirect_uri: {redirect_uri}")
    logger.info(f"Client ID: {client_id[:10]}..." if client_id else "Client ID: None")
    
    # SoundCloud OAuth authorization endpoint
    auth_url = "https://soundcloud.com/connect"
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "non-expiring",  # Request non-expiring access
        "state": state
    }
    
    # Build URL with query parameters
    from urllib.parse import urlencode
    final_url = f"{auth_url}?{urlencode(params)}"
    logger.info(f"Generated SoundCloud authorization URL: {auth_url}?client_id={client_id[:10]}...&redirect_uri={redirect_uri}&...")
    
    return final_url


async def exchange_code_for_token(code: str) -> Optional[Dict]:
    """
    Exchange authorization code for access token.
    
    Args:
        code: Authorization code from SoundCloud callback
        
    Returns:
        Dictionary with access_token, refresh_token, expires_in, etc.
        Returns None if exchange fails
    """
    client_id = settings.SOUNDCLOUD_CLIENT_ID
    client_secret = settings.SOUNDCLOUD_CLIENT_SECRET
    redirect_uri = settings.SOUNDCLOUD_REDIRECT_URI
    
    if not client_id or not client_secret or not redirect_uri:
        logger.error("SoundCloud OAuth credentials not configured")
        return None
    
    token_url = "https://api.soundcloud.com/oauth2/token"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Successfully exchanged code for token")
                return data
            else:
                error_text = response.text[:200]
                # Check if it's an "invalid_grant" error (expected when code is reused)
                if "invalid_grant" in error_text.lower():
                    logger.warning(
                        f"Token exchange failed with invalid_grant (code may have been reused): "
                        f"{response.status_code} - {error_text}"
                    )
                else:
                    logger.error(f"Token exchange failed: {response.status_code} - {error_text}")
                return None
                
        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}", exc_info=True)
            return None


async def get_soundcloud_user_info(access_token: str) -> Optional[Dict]:
    """
    Get user information from SoundCloud API using access token.
    
    Args:
        access_token: OAuth access token
        
    Returns:
        Dictionary with user info (id, username, full_name, avatar_url, etc.)
        Returns None if request fails
    """
    api_url = "https://api.soundcloud.com/me"
    
    headers = {
        "Authorization": f"OAuth {access_token}"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                api_url,
                headers=headers,
                timeout=30.0,
                follow_redirects=True
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched SoundCloud user info: {data.get('username')}")
                return data
            else:
                logger.error(f"Failed to get user info: {response.status_code} - {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting SoundCloud user info: {str(e)}", exc_info=True)
            return None


async def refresh_soundcloud_token(refresh_token: str) -> Optional[Dict]:
    """
    Refresh an expired SoundCloud access token.
    
    Args:
        refresh_token: Refresh token from initial OAuth flow
        
    Returns:
        Dictionary with new access_token, expires_in, etc.
        Returns None if refresh fails
    """
    client_id = settings.SOUNDCLOUD_CLIENT_ID
    client_secret = settings.SOUNDCLOUD_CLIENT_SECRET
    
    if not client_id or not client_secret:
        logger.error("SoundCloud OAuth credentials not configured")
        return None
    
    token_url = "https://api.soundcloud.com/oauth2/token"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Successfully refreshed SoundCloud token")
                return data
            else:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}", exc_info=True)
            return None
