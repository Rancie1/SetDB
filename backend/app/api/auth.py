"""
Authentication API routes.

Handles user registration, login, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import secrets
from typing import Dict, Set
import logging

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token
from app.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_active_user
)
from app.core.exceptions import UnauthorizedError, DuplicateEntryError
from app.services.soundcloud_oauth import (
    get_soundcloud_oauth_url,
    exchange_code_for_token,
    get_soundcloud_user_info
)
from app.services.google_oauth import (
    get_google_oauth_url,
    exchange_code_for_token as google_exchange_code_for_token,
    get_google_user_info,
    get_google_user_info_with_refresh,
    ensure_valid_google_token,
    GoogleOAuthConfigurationError,
    GoogleOAuthAPIError
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory state store for CSRF protection
# In production, this should be replaced with Redis or database storage
_oauth_states: Dict[str, datetime] = {}
_STATE_EXPIRY_MINUTES = 10

def _cleanup_expired_states():
    """Remove expired state tokens from memory."""
    now = datetime.utcnow()
    expired_states = [
        state for state, expiry in _oauth_states.items()
        if now > expiry
    ]
    for state in expired_states:
        del _oauth_states[state]

def _store_state(state: str) -> None:
    """Store a state token with expiration."""
    _cleanup_expired_states()
    expiry = datetime.utcnow() + timedelta(minutes=_STATE_EXPIRY_MINUTES)
    _oauth_states[state] = expiry

def _validate_and_consume_state(state: str) -> bool:
    """Validate and consume a state token (one-time use)."""
    _cleanup_expired_states()
    if state in _oauth_states:
        del _oauth_states[state]  # Consume the state token
        return True
    return False


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    Creates a new user account with hashed password.
    Returns the created user (without password).
    """
    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise DuplicateEntryError(f"Username {user_data.username} already exists")
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise DuplicateEntryError(f"Email {user_data.email} already exists")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        display_name=user_data.display_name,
        bio=user_data.bio,
        avatar_url=user_data.avatar_url
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login and get access token.
    
    Uses OAuth2PasswordRequestForm which expects:
    - username: Can be username or email
    - password: Plain text password
    
    Returns a JWT access token.
    """
    # Try to find user by username or email
    result = await db.execute(
        select(User).where(
            (User.username == form_data.username) |
            (User.email == form_data.username)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise UnauthorizedError("Incorrect username or password")
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise UnauthorizedError("Incorrect username or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.
    
    Returns the user object for the authenticated user.
    """
    return current_user


@router.get("/soundcloud/authorize")
async def soundcloud_authorize():
    """
    Get SoundCloud OAuth authorization URL.
    
    Returns a URL that the frontend should redirect the user to.
    The state parameter is stored server-side for CSRF protection.
    """
    # Generate a random state token for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state server-side for validation
    _store_state(state)
    
    try:
        auth_url = get_soundcloud_oauth_url(state)
        return {
            "authorization_url": auth_url,
            "state": state  # Frontend should include this in callback
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


@router.get("/soundcloud/debug")
async def soundcloud_debug():
    """
    Debug endpoint to check SoundCloud OAuth configuration.
    
    Returns the authorization URL that would be generated (without redirecting).
    Useful for verifying the redirect URI matches SoundCloud's portal.
    """
    from app.services.soundcloud_oauth import get_soundcloud_oauth_url
    from app.config import settings
    
    try:
        state = "debug_state_token"
        auth_url = get_soundcloud_oauth_url(state)
        
        # Parse the URL to show components
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(auth_url)
        params = parse_qs(parsed.query)
        
        return {
            "status": "Configuration looks good",
            "redirect_uri": settings.SOUNDCLOUD_REDIRECT_URI,
            "client_id": settings.SOUNDCLOUD_CLIENT_ID[:10] + "..." if settings.SOUNDCLOUD_CLIENT_ID else None,
            "authorization_url": auth_url,
            "parsed_redirect_uri": params.get("redirect_uri", [None])[0],
            "instructions": "Copy the 'redirect_uri' value above and verify it matches EXACTLY in SoundCloud's developer portal"
        }
    except ValueError as e:
        return {
            "status": "Configuration error",
            "error": str(e),
            "redirect_uri": settings.SOUNDCLOUD_REDIRECT_URI,
            "client_id": settings.SOUNDCLOUD_CLIENT_ID[:10] + "..." if settings.SOUNDCLOUD_CLIENT_ID else None,
        }


@router.post("/soundcloud/callback", response_model=Token)
async def soundcloud_callback(
    code: str,
    state: str,  # State parameter from OAuth callback
    db: AsyncSession = Depends(get_db)
):
    """
    Handle SoundCloud OAuth callback.
    
    Validates the state parameter for CSRF protection, then exchanges 
    the authorization code for an access token, fetches user info from SoundCloud, 
    and either:
    - Creates a new user account if they don't exist
    - Logs in existing user if they already have an account
    
    Returns a JWT access token for the SetDB app.
    """
    # Validate state parameter for CSRF protection
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing state parameter. Possible CSRF attack."
        )
    
    if not _validate_and_consume_state(state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter. Possible CSRF attack."
        )
    
    # Exchange code for token
    token_data = await exchange_code_for_token(code)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code for token"
        )
    
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No access token received from SoundCloud"
        )
    
    # Get user info from SoundCloud
    soundcloud_user = await get_soundcloud_user_info(access_token)
    if not soundcloud_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch user information from SoundCloud"
        )
    
    soundcloud_user_id = str(soundcloud_user.get("id"))
    soundcloud_username = soundcloud_user.get("username", "")
    soundcloud_full_name = soundcloud_user.get("full_name", "")
    soundcloud_avatar = soundcloud_user.get("avatar_url", "")
    
    # Check if user already exists by SoundCloud ID
    result = await db.execute(
        select(User).where(User.soundcloud_user_id == soundcloud_user_id)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        # Update tokens and user info
        existing_user.soundcloud_access_token = access_token
        existing_user.soundcloud_refresh_token = refresh_token
        if soundcloud_avatar:
            existing_user.avatar_url = soundcloud_avatar
        if soundcloud_full_name and not existing_user.display_name:
            existing_user.display_name = soundcloud_full_name
        
        # Fix email domain if it's using .local (for Pydantic validation)
        if existing_user.email and existing_user.email.endswith("@soundcloud.local"):
            # Update to .oauth domain
            base_email = existing_user.email.replace("@soundcloud.local", "")
            existing_user.email = f"{base_email}@soundcloud.oauth"
        
        await db.commit()
        await db.refresh(existing_user)
        
        # Create JWT token
        jwt_token = create_access_token(data={"sub": str(existing_user.id)})
        return {"access_token": jwt_token, "token_type": "bearer"}
    
    # Create new user
    # Generate username from SoundCloud username (make it unique)
    base_username = soundcloud_username.lower().replace(" ", "_")
    username = base_username
    counter = 1
    
    # Ensure username is unique
    while True:
        result = await db.execute(select(User).where(User.username == username))
        if not result.scalar_one_or_none():
            break
        username = f"{base_username}_{counter}"
        counter += 1
    
    # Generate a fake email (SoundCloud doesn't provide email)
    # Users can update this later
    # Using .oauth domain instead of .local to pass Pydantic email validation
    email = f"{username}@soundcloud.oauth"
    
    # Ensure email is unique
    counter = 1
    while True:
        result = await db.execute(select(User).where(User.email == email))
        if not result.scalar_one_or_none():
            break
        email = f"{username}_{counter}@soundcloud.oauth"
        counter += 1
    
    new_user = User(
        username=username,
        email=email,
        hashed_password=None,  # OAuth users don't have passwords
        display_name=soundcloud_full_name or soundcloud_username,
        avatar_url=soundcloud_avatar,
        soundcloud_user_id=soundcloud_user_id,
        soundcloud_access_token=access_token,
        soundcloud_refresh_token=refresh_token
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create JWT token
    jwt_token = create_access_token(data={"sub": str(new_user.id)})
    return {"access_token": jwt_token, "token_type": "bearer"}


@router.get("/google/authorize")
async def google_authorize():
    """
    Get Google OAuth authorization URL.
    
    Returns a URL that the frontend should redirect the user to.
    The state parameter is stored server-side for CSRF protection.
    """
    # Generate a random state token for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state server-side for validation
    _store_state(state)
    
    try:
        auth_url = get_google_oauth_url(state)
        return {
            "authorization_url": auth_url,
            "state": state  # Frontend should include this in callback
        }
    except GoogleOAuthConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in google_authorize: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.get("/google/debug")
async def google_debug():
    """
    Debug endpoint to check Google OAuth configuration.
    
    Returns the authorization URL that would be generated (without redirecting).
    Useful for verifying the redirect URI matches Google's OAuth configuration.
    """
    from app.config import settings
    
    try:
        # Check configuration validation
        is_valid, errors = settings.validate_google_oauth_config()
        
        if not is_valid:
            return {
                "status": "Configuration error",
                "errors": errors,
                "environment": settings.ENVIRONMENT,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "client_id": settings.GOOGLE_CLIENT_ID[:10] + "..." if settings.GOOGLE_CLIENT_ID else None,
            }
        
        state = "debug_state_token"
        auth_url = get_google_oauth_url(state)
        
        # Parse the URL to show components
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(auth_url)
        params = parse_qs(parsed.query)
        
        return {
            "status": "Configuration looks good",
            "environment": settings.ENVIRONMENT,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "client_id": settings.GOOGLE_CLIENT_ID[:10] + "..." if settings.GOOGLE_CLIENT_ID else None,
            "authorization_url": auth_url,
            "parsed_redirect_uri": params.get("redirect_uri", [None])[0],
            "instructions": "Copy the 'redirect_uri' value above and verify it matches EXACTLY in Google's OAuth configuration"
        }
    except GoogleOAuthConfigurationError as e:
        return {
            "status": "Configuration error",
            "error": str(e),
            "environment": settings.ENVIRONMENT,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "client_id": settings.GOOGLE_CLIENT_ID[:10] + "..." if settings.GOOGLE_CLIENT_ID else None,
        }
    except Exception as e:
        logger.error(f"Unexpected error in google_debug: {str(e)}", exc_info=True)
        return {
            "status": "Unexpected error",
            "error": str(e),
            "environment": settings.ENVIRONMENT,
        }


@router.get("/google/config")
async def google_config_status():
    """
    Check if Google OAuth is properly configured.
    
    Returns configuration status for frontend to conditionally show Google sign-in button.
    Does not expose sensitive configuration details.
    """
    from app.config import settings
    
    is_configured = settings.is_google_oauth_configured()
    is_valid, errors = settings.validate_google_oauth_config()
    
    return {
        "configured": is_configured,
        "valid": is_valid,
        "environment": settings.ENVIRONMENT,
        "error_count": len(errors) if not is_valid else 0
    }


@router.post("/google/callback", response_model=Token)
async def google_callback(
    code: str,
    state: str,  # State parameter from OAuth callback
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Google OAuth callback.
    
    Validates the state parameter for CSRF protection, then exchanges 
    the authorization code for an access token, fetches user info from Google, 
    and either:
    - Creates a new user account if they don't exist
    - Links Google credentials to existing account if email matches
    - Logs in existing user if they already have Google linked
    
    Returns a JWT access token for the SetDB app.
    """
    # Validate state parameter for CSRF protection
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing state parameter. Possible CSRF attack."
        )
    
    if not _validate_and_consume_state(state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter. Possible CSRF attack."
        )
    
    # Exchange code for token
    try:
        token_data = await google_exchange_code_for_token(code)
    except GoogleOAuthConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except GoogleOAuthAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during token exchange: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during authentication. Please try again."
        )
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code for token. Please try signing in again."
        )
    
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No access token received from Google. Please try signing in again."
        )
    
    # Calculate token expiration time
    token_expires_at = None
    if expires_in:
        from datetime import datetime, timedelta
        token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    
    # Get user info from Google
    try:
        google_user = await get_google_user_info(access_token)
    except GoogleOAuthAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during user info fetch: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching user information. Please try again."
        )
    
    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch user information from Google. Please try signing in again."
        )
    
    google_user_id = str(google_user.get("id"))
    google_email = google_user.get("email", "")
    google_name = google_user.get("name", "")
    google_picture = google_user.get("picture", "")
    
    try:
        # Check if user already exists by Google ID
        result = await db.execute(
            select(User).where(User.google_user_id == google_user_id)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            # Update tokens and user info
            existing_user.google_access_token = access_token
            existing_user.google_refresh_token = refresh_token
            existing_user.google_token_expires_at = token_expires_at
            if google_picture and not existing_user.avatar_url:
                existing_user.avatar_url = google_picture
            if google_name and not existing_user.display_name:
                existing_user.display_name = google_name
            
            await db.commit()
            await db.refresh(existing_user)
            
            # Create JWT token
            jwt_token = create_access_token(data={"sub": str(existing_user.id)})
            return {"access_token": jwt_token, "token_type": "bearer"}
        
        # Check if user exists by email (for account linking)
        if google_email:
            result = await db.execute(
                select(User).where(User.email == google_email)
            )
            existing_user_by_email = result.scalar_one_or_none()
            
            if existing_user_by_email:
                # Link Google credentials to existing account
                existing_user_by_email.google_user_id = google_user_id
                existing_user_by_email.google_access_token = access_token
                existing_user_by_email.google_refresh_token = refresh_token
                existing_user_by_email.google_token_expires_at = token_expires_at
                if google_picture and not existing_user_by_email.avatar_url:
                    existing_user_by_email.avatar_url = google_picture
                if google_name and not existing_user_by_email.display_name:
                    existing_user_by_email.display_name = google_name
                
                await db.commit()
                await db.refresh(existing_user_by_email)
                
                # Create JWT token
                jwt_token = create_access_token(data={"sub": str(existing_user_by_email.id)})
                return {"access_token": jwt_token, "token_type": "bearer"}
        
        # Create new user
        # Generate username from Google name or email
        if google_name:
            base_username = google_name.lower().replace(" ", "_")
        elif google_email:
            base_username = google_email.split("@")[0].lower()
        else:
            base_username = "google_user"
        
        # Remove non-alphanumeric characters except underscores
        import re
        base_username = re.sub(r'[^a-z0-9_]', '', base_username)
        
        username = base_username
        counter = 1
        
        # Ensure username is unique
        while True:
            result = await db.execute(select(User).where(User.username == username))
            if not result.scalar_one_or_none():
                break
            username = f"{base_username}_{counter}"
            counter += 1
        
        # Use Google email or generate a placeholder
        email = google_email if google_email else f"{username}@google.oauth"
        
        # Ensure email is unique (shouldn't happen with Google emails, but just in case)
        counter = 1
        while True:
            result = await db.execute(select(User).where(User.email == email))
            if not result.scalar_one_or_none():
                break
            email = f"{username}_{counter}@google.oauth"
            counter += 1
        
        new_user = User(
            username=username,
            email=email,
            hashed_password=None,  # OAuth users don't have passwords
            display_name=google_name or username,
            avatar_url=google_picture,
            google_user_id=google_user_id,
            google_access_token=access_token,
            google_refresh_token=refresh_token,
            google_token_expires_at=token_expires_at
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        # Create JWT token
        jwt_token = create_access_token(data={"sub": str(new_user.id)})
        return {"access_token": jwt_token, "token_type": "bearer"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Database error during Google OAuth callback: {str(e)}", exc_info=True)
        
        # Check for specific database errors
        if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this Google profile already exists or there was a conflict creating your account. Please try again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occurred while creating your account. Please try again later."
            )


@router.get("/google/profile")
async def get_google_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's Google profile information.
    
    This endpoint demonstrates secure token management by automatically
    refreshing expired tokens when needed.
    
    Returns the user's Google profile data or an error if not linked.
    """
    if not current_user.google_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is not linked to Google. Please sign in with Google first."
        )
    
    try:
        # This will automatically refresh the token if needed
        google_user_info = await get_google_user_info_with_refresh(current_user, db)
        
        if not google_user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch Google profile information."
            )
        
        return {
            "google_user_id": google_user_info.get("id"),
            "email": google_user_info.get("email"),
            "name": google_user_info.get("name"),
            "picture": google_user_info.get("picture"),
            "verified_email": google_user_info.get("verified_email"),
            "token_expires_at": current_user.google_token_expires_at.isoformat() if current_user.google_token_expires_at else None
        }
        
    except GoogleOAuthAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching Google profile for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching your Google profile. Please try again."
        )


@router.post("/google/refresh-token")
async def refresh_google_access_token(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually refresh the user's Google access token.
    
    This endpoint allows manual token refresh and demonstrates
    the secure token management functionality.
    
    Returns the new token expiration time.
    """
    if not current_user.google_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is not linked to Google. Please sign in with Google first."
        )
    
    try:
        # This will refresh the token if needed
        await ensure_valid_google_token(current_user, db)
        
        return {
            "message": "Google access token refreshed successfully",
            "token_expires_at": current_user.google_token_expires_at.isoformat() if current_user.google_token_expires_at else None
        }
        
    except GoogleOAuthAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error refreshing Google token for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while refreshing your Google token. Please try again."
        )

