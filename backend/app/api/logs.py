"""
Log API routes.

Handles logging sets (adding to user's diary), viewing logs, and updating logs.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.models import UserSetLog, User, DJSet
from app.schemas import LogCreate, LogUpdate, LogResponse, PaginatedResponse
from app.auth import get_current_active_user
from app.core.exceptions import DuplicateEntryError

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.post("", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
async def log_set(
    log_data: LogCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Log a set (add to user's diary).
    
    This creates a record that the user has watched/listened to a set.
    """
    # Check if set exists
    result = await db.execute(select(DJSet).where(DJSet.id == log_data.set_id))
    set_obj = result.scalar_one_or_none()
    
    if not set_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Set with ID {log_data.set_id} not found"
        )
    
    # Check if already logged
    existing = await db.execute(
        select(UserSetLog).where(
            UserSetLog.user_id == current_user.id,
            UserSetLog.set_id == log_data.set_id
        )
    )
    if existing.scalar_one_or_none():
        raise DuplicateEntryError("Set already logged")
    
    # Create log entry
    new_log = UserSetLog(
        user_id=current_user.id,
        set_id=log_data.set_id,
        watched_date=log_data.watched_date
    )
    
    db.add(new_log)
    await db.commit()
    await db.refresh(new_log)
    
    return new_log


@router.get("/users/{user_id}", response_model=PaginatedResponse)
async def get_user_logs(
    user_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of sets logged by a user."""
    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Build query
    query = select(UserSetLog).where(UserSetLog.user_id == user_id).order_by(UserSetLog.watched_date.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    return PaginatedResponse(
        items=list(logs),
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.put("/{log_id}", response_model=LogResponse)
async def update_log(
    log_id: UUID,
    log_update: LogUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a log entry (only if it belongs to the current user)."""
    result = await db.execute(select(UserSetLog).where(UserSetLog.id == log_id))
    log_obj = result.scalar_one_or_none()
    
    if not log_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log with ID {log_id} not found"
        )
    
    # Check ownership
    if log_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this log"
        )
    
    # Update fields
    if log_update.watched_date is not None:
        log_obj.watched_date = log_update.watched_date
    
    await db.commit()
    await db.refresh(log_obj)
    
    return log_obj


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log(
    log_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a log entry (only if it belongs to the current user)."""
    result = await db.execute(select(UserSetLog).where(UserSetLog.id == log_id))
    log_obj = result.scalar_one_or_none()
    
    if not log_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log with ID {log_id} not found"
        )
    
    # Check ownership
    if log_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this log"
        )
    
    await db.delete(log_obj)
    await db.commit()
    
    return None

