"""
Google OAuth service.

Handles OAuth2 Authorization Code flow for user authentication.
Follows the same patterns as SoundCloud OAuth for consistency.
"""

import httpx
import logging
from typing import Optional, Dict
from app.config import settings

logger = logging.getLogger(__name__)


class GoogleOAuthConfigurationError(Exception):
    """Raised when Google OAuth is not properly configured."""
    pass


class GoogleOAuthAPIError(Exception):
    """Raised when Google OAuth API requests fail."""
    pass


def get_google_oauth_url(state: str) -> str:
    """
    Generate Google OAuth authorization URL.
    
    Args:
        state: CSRF protection token (should be stored in session)
        
    Returns:
        URL to redirect user to for authorization
        
    Raises:
        GoogleOAuthConfigurationError: If OAuth credentials are not configured
    """
    # Validate configuration before proceeding
    is_valid, errors = settings.validate_google_oauth_config()
    if not is_valid:
        error_msg = "Google OAuth is not properly configured: " + "; ".join(errors)
        raise GoogleOAuthConfigurationError(error_msg)
    
    client_id = settings.GOOGLE_CLIENT_ID
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    
    # Log configuration for debugging (don't log full client_id in production)
    logger.info(f"Generating Google OAuth URL with redirect_uri: {redirect_uri}")
    logger.info(f"Client ID: {client_id[:10]}..." if client_id else "Client ID: None")
    
    # Google OAuth authorization endpoint
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",  # Request basic profile information
        "state": state,
        "access_type": "offline",  # Request refresh token
        "prompt": "consent"  # Force consent screen to ensure refresh token
    }
    
    # Build URL with query parameters
    from urllib.parse import urlencode
    final_url = f"{auth_url}?{urlencode(params)}"
    logger.info(f"Generated Google authorization URL: {auth_url}?client_id={client_id[:10]}...&redirect_uri={redirect_uri}&...")
    
    return final_url


async def exchange_code_for_token(code: str) -> Optional[Dict]:
    """
    Exchange authorization code for access token.
    
    Args:
        code: Authorization code from Google callback
        
    Returns:
        Dictionary with access_token, refresh_token, expires_in, etc.
        Returns None if exchange fails
        
    Raises:
        GoogleOAuthConfigurationError: If OAuth credentials are not configured
        GoogleOAuthAPIError: If Google API request fails with detailed error
    """
    # Validate configuration before proceeding
    is_valid, errors = settings.validate_google_oauth_config()
    if not is_valid:
        error_msg = "Google OAuth is not properly configured: " + "; ".join(errors)
        raise GoogleOAuthConfigurationError(error_msg)
    
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    
    token_url = "https://oauth2.googleapis.com/token"
    
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
                    raise GoogleOAuthAPIError("Authorization code is invalid or has already been used. Please try signing in again.")
                elif "invalid_client" in error_text.lower():
                    logger.error(f"Token exchange failed with invalid_client: {response.status_code} - {error_text}")
                    raise GoogleOAuthConfigurationError("Google OAuth client credentials are invalid. Please check your configuration.")
                else:
                    logger.error(f"Token exchange failed: {response.status_code} - {error_text}")
                    raise GoogleOAuthAPIError(f"Failed to exchange authorization code for token. Google returned: {error_text}")
                
        except httpx.TimeoutException:
            logger.error("Token exchange request timed out")
            raise GoogleOAuthAPIError("Request to Google timed out. Please try again.")
        except httpx.NetworkError as e:
            logger.error(f"Network error during token exchange: {str(e)}")
            raise GoogleOAuthAPIError("Network error occurred while connecting to Google. Please check your internet connection and try again.")
        except Exception as e:
            if isinstance(e, (GoogleOAuthConfigurationError, GoogleOAuthAPIError)):
                raise  # Re-raise our custom exceptions
            logger.error(f"Unexpected error exchanging code for token: {str(e)}", exc_info=True)
            raise GoogleOAuthAPIError("An unexpected error occurred during authentication. Please try again.")


async def get_google_user_info(access_token: str) -> Optional[Dict]:
    """
    Get user information from Google API using access token.
    
    Args:
        access_token: OAuth access token
        
    Returns:
        Dictionary with user info (sub, email, name, picture, etc.)
        Returns None if request fails
        
    Raises:
        GoogleOAuthAPIError: If Google API request fails with detailed error
    """
    api_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
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
                logger.info(f"Successfully fetched Google user info: {data.get('email')}")
                return data
            elif response.status_code == 401:
                logger.error(f"Unauthorized access to user info: {response.status_code} - {response.text[:200]}")
                raise GoogleOAuthAPIError("Access token is invalid or expired. Please sign in again.")
            else:
                error_text = response.text[:200]
                logger.error(f"Failed to get user info: {response.status_code} - {error_text}")
                raise GoogleOAuthAPIError(f"Failed to fetch user information from Google. Status: {response.status_code}")
                
        except httpx.TimeoutException:
            logger.error("User info request timed out")
            raise GoogleOAuthAPIError("Request to Google timed out. Please try again.")
        except httpx.NetworkError as e:
            logger.error(f"Network error during user info fetch: {str(e)}")
            raise GoogleOAuthAPIError("Network error occurred while fetching user information. Please check your internet connection and try again.")
        except Exception as e:
            if isinstance(e, GoogleOAuthAPIError):
                raise  # Re-raise our custom exceptions
            logger.error(f"Unexpected error getting Google user info: {str(e)}", exc_info=True)
            raise GoogleOAuthAPIError("An unexpected error occurred while fetching user information. Please try again.")


async def refresh_google_token(refresh_token: str) -> Optional[Dict]:
    """
    Refresh an expired Google access token.
    
    Args:
        refresh_token: Refresh token from initial OAuth flow
        
    Returns:
        Dictionary with new access_token, expires_in, etc.
        Returns None if refresh fails
        
    Raises:
        GoogleOAuthConfigurationError: If OAuth credentials are not configured
        GoogleOAuthAPIError: If Google API request fails with detailed error
    """
    # Validate configuration before proceeding
    is_valid, errors = settings.validate_google_oauth_config()
    if not is_valid:
        error_msg = "Google OAuth is not properly configured: " + "; ".join(errors)
        raise GoogleOAuthConfigurationError(error_msg)
    
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    
    token_url = "https://oauth2.googleapis.com/token"
    
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
                logger.info("Successfully refreshed Google token")
                return data
            elif response.status_code == 400:
                error_text = response.text[:200]
                if "invalid_grant" in error_text.lower():
                    logger.warning(f"Token refresh failed with invalid_grant: {response.status_code} - {error_text}")
                    raise GoogleOAuthAPIError("Refresh token is invalid or expired. Please sign in again.")
                else:
                    logger.error(f"Token refresh failed: {response.status_code} - {error_text}")
                    raise GoogleOAuthAPIError(f"Failed to refresh access token. Google returned: {error_text}")
            else:
                error_text = response.text[:200]
                logger.error(f"Token refresh failed: {response.status_code} - {error_text}")
                raise GoogleOAuthAPIError(f"Failed to refresh access token. Status: {response.status_code}")
                
        except httpx.TimeoutException:
            logger.error("Token refresh request timed out")
            raise GoogleOAuthAPIError("Request to Google timed out. Please try again.")
        except httpx.NetworkError as e:
            logger.error(f"Network error during token refresh: {str(e)}")
            raise GoogleOAuthAPIError("Network error occurred while refreshing token. Please check your internet connection and try again.")
        except Exception as e:
            if isinstance(e, (GoogleOAuthConfigurationError, GoogleOAuthAPIError)):
                raise  # Re-raise our custom exceptions
            logger.error(f"Unexpected error refreshing token: {str(e)}", exc_info=True)
            raise GoogleOAuthAPIError("An unexpected error occurred while refreshing token. Please try again.")


async def update_user_tokens(user, db_session, access_token: str, refresh_token: Optional[str] = None, expires_in: Optional[int] = None):
    """
    Update user's Google tokens in the database securely.
    
    Args:
        user: User model instance
        db_session: Database session
        access_token: New access token
        refresh_token: New refresh token (optional)
        expires_in: Token expiration time in seconds (optional)
    """
    from datetime import datetime, timedelta
    
    user.google_access_token = access_token
    
    if refresh_token:
        user.google_refresh_token = refresh_token
    
    if expires_in:
        user.google_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    
    await db_session.commit()
    await db_session.refresh(user)
    logger.info(f"Updated Google tokens for user {user.id}")


async def ensure_valid_google_token(user, db_session) -> str:
    """
    Ensure user has a valid Google access token, refreshing if necessary.
    
    Args:
        user: User model instance with Google OAuth fields
        db_session: Database session
        
    Returns:
        Valid access token
        
    Raises:
        GoogleOAuthAPIError: If token refresh fails or user has no refresh token
    """
    from datetime import datetime, timedelta
    
    # Check if user has Google credentials
    if not user.google_access_token:
        raise GoogleOAuthAPIError("User has no Google access token. Please sign in with Google.")
    
    # Check if token is expired (with 5-minute buffer)
    if user.google_token_expires_at:
        buffer_time = datetime.utcnow() + timedelta(minutes=5)
        if user.google_token_expires_at <= buffer_time:
            logger.info(f"Google token for user {user.id} is expired or expiring soon, attempting refresh")
            
            # Try to refresh the token
            if not user.google_refresh_token:
                raise GoogleOAuthAPIError("Google access token is expired and no refresh token available. Please sign in again.")
            
            try:
                token_data = await refresh_google_token(user.google_refresh_token)
                if not token_data:
                    raise GoogleOAuthAPIError("Failed to refresh Google access token. Please sign in again.")
                
                # Update user tokens
                new_access_token = token_data.get("access_token")
                new_refresh_token = token_data.get("refresh_token")  # May be None
                expires_in = token_data.get("expires_in")
                
                if not new_access_token:
                    raise GoogleOAuthAPIError("No access token received during refresh. Please sign in again.")
                
                await update_user_tokens(
                    user, 
                    db_session, 
                    new_access_token, 
                    new_refresh_token, 
                    expires_in
                )
                
                return new_access_token
                
            except GoogleOAuthAPIError:
                # Clear invalid tokens
                user.google_access_token = None
                user.google_refresh_token = None
                user.google_token_expires_at = None
                await db_session.commit()
                raise
            except Exception as e:
                logger.error(f"Unexpected error during token refresh for user {user.id}: {str(e)}", exc_info=True)
                raise GoogleOAuthAPIError("An unexpected error occurred while refreshing your Google token. Please sign in again.")
    
    return user.google_access_token


async def get_google_user_info_with_refresh(user, db_session) -> Optional[Dict]:
    """
    Get Google user info, automatically refreshing token if needed.
    
    Args:
        user: User model instance with Google OAuth fields
        db_session: Database session
        
    Returns:
        Dictionary with user info from Google
        
    Raises:
        GoogleOAuthAPIError: If unable to get valid token or user info
    """
    try:
        # Ensure we have a valid token
        access_token = await ensure_valid_google_token(user, db_session)
        
        # Get user info with the valid token
        return await get_google_user_info(access_token)
        
    except GoogleOAuthAPIError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting Google user info for user {user.id}: {str(e)}", exc_info=True)
        raise GoogleOAuthAPIError("An unexpected error occurred while fetching your Google profile. Please try again.")