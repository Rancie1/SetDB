"""
Authentication utilities for JWT tokens and password hashing.

This module provides:
- Password hashing and verification (bcrypt)
- JWT token creation and validation
- FastAPI dependencies for authentication
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User
from app.core.exceptions import UnauthorizedError

# OAuth2 scheme for token extraction
# This tells FastAPI to look for the token in the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The password in plain text
        hashed_password: The hashed password from database
        
    Returns:
        True if passwords match, False otherwise
    """
    # Convert string password to bytes if needed
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    
    # Convert hashed password to bytes if it's a string
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    # Convert password to bytes
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password, salt)
    
    # Return as string
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing user data (typically user_id)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    
    # Encode the token with the secret key
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    
    This function:
    1. Extracts the token from the Authorization header
    2. Decodes and validates the token
    3. Fetches the user from the database
    4. Returns the user object
    
    Args:
        token: JWT token from Authorization header (injected by FastAPI)
        db: Database session (injected by FastAPI)
        
    Returns:
        User object
        
    Raises:
        UnauthorizedError: If token is invalid or user not found
    """
    credentials_exception = UnauthorizedError("Could not validate credentials")
    
    try:
        # Decode the token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Extract user_id from token
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Fetch user from database
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure the current user is active.
    
    This is a placeholder for future use (e.g., if you add
    an 'is_active' field to the User model).
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        Active user object
    """
    # Future: Add is_active check here
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


