"""
Authentication API routes.

Handles user registration, login, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
import secrets

router = APIRouter(prefix="/api/auth", tags=["auth"])


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
    The frontend should store the 'state' parameter for CSRF protection.
    """
    # Generate a random state token for CSRF protection
    state = secrets.token_urlsafe(32)
    
    try:
        auth_url = get_soundcloud_oauth_url(state)
        return {
            "authorization_url": auth_url,
            "state": state  # Frontend should store this and verify it in callback
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
    state: str,  # Frontend should send the state back for verification
    db: AsyncSession = Depends(get_db)
):
    """
    Handle SoundCloud OAuth callback.
    
    Exchanges the authorization code for an access token,
    fetches user info from SoundCloud, and either:
    - Creates a new user account if they don't exist
    - Logs in existing user if they already have an account
    
    Returns a JWT access token for the SetDB app.
    """
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

