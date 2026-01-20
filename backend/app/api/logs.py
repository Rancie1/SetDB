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
from app.models import UserSetLog, User, DJSet, SourceType
from app.schemas import LogCreate, LogUpdate, LogResponse, PaginatedResponse
from app.auth import get_current_active_user
from app.core.exceptions import DuplicateEntryError

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/users/{user_id}/top-sets", response_model=list)
async def get_user_top_sets(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a user's top 5 sets.
    
    Returns the sets marked as top sets, ordered by top_set_order.
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Get top sets ordered by top_set_order
    query = (
        select(UserSetLog)
        .join(DJSet, UserSetLog.set_id == DJSet.id)
        .where(
            UserSetLog.user_id == user_id,
            UserSetLog.is_top_set == True
        )
        .order_by(UserSetLog.top_set_order.asc())
        .limit(5)
    )
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Load set relationships and convert to response schemas
    from app.schemas import LogResponse, DJSetResponse
    top_sets = []
    for log in logs:
        await db.refresh(log, ["set"])
        log_dict = LogResponse.model_validate(log).model_dump()
        if log.set:
            log_dict['set'] = DJSetResponse.model_validate(log.set).model_dump()
        top_sets.append(log_dict)
    
    return top_sets


@router.post("/{log_id}/set-top", response_model=LogResponse)
async def set_top_set(
    log_id: UUID,
    order: int = Query(..., ge=1, le=5, description="Order position (1-5)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a logged set as a top set and assign it an order (1-5).
    
    If another set already has this order, it will be unmarked as top set.
    """
    # Get the log entry
    result = await db.execute(
        select(UserSetLog).where(UserSetLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log entry not found"
        )
    
    # Check ownership
    if log.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own top sets"
        )
    
    # Check if user already has 5 top sets (excluding current log if it's already a top set)
    existing_top_count = await db.execute(
        select(func.count(UserSetLog.id)).where(
            UserSetLog.user_id == current_user.id,
            UserSetLog.is_top_set == True,
            UserSetLog.id != log_id  # Exclude current log
        )
    )
    count = existing_top_count.scalar() or 0
    
    # If this log is not already a top set and user has 5 top sets, unmark the one with the target order
    if not log.is_top_set and count >= 5:
        # Find the log with the target order
        existing_order_log = await db.execute(
            select(UserSetLog).where(
                UserSetLog.user_id == current_user.id,
                UserSetLog.is_top_set == True,
                UserSetLog.top_set_order == order,
                UserSetLog.id != log_id
            )
        )
        existing_log = existing_order_log.scalar_one_or_none()
        if existing_log:
            existing_log.is_top_set = False
            existing_log.top_set_order = None
    
    # If another log already has this order (and it's not the current log), unmark it
    existing_order_log = await db.execute(
        select(UserSetLog).where(
            UserSetLog.user_id == current_user.id,
            UserSetLog.is_top_set == True,
            UserSetLog.top_set_order == order,
            UserSetLog.id != log_id
        )
    )
    existing_log = existing_order_log.scalar_one_or_none()
    if existing_log:
        existing_log.is_top_set = False
        existing_log.top_set_order = None
    
    # Mark this log as top set with the specified order
    log.is_top_set = True
    log.top_set_order = order
    
    await db.commit()
    await db.refresh(log, ["set"])
    
    # Convert to response schema
    from app.schemas import LogResponse, DJSetResponse
    log_dict = LogResponse.model_validate(log).model_dump()
    if log.set:
        log_dict['set'] = DJSetResponse.model_validate(log.set).model_dump()
    
    return LogResponse(**log_dict)


@router.delete("/{log_id}/unset-top", status_code=status.HTTP_204_NO_CONTENT)
async def unset_top_set(
    log_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a set from top sets.
    """
    # Get the log entry
    result = await db.execute(
        select(UserSetLog).where(UserSetLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log entry not found"
        )
    
    # Check ownership
    if log.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own top sets"
        )
    
    # Unmark as top set
    log.is_top_set = False
    log.top_set_order = None
    
    await db.commit()
    
    return None


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
    await db.refresh(new_log, ["set"])
    
    # Convert to response schema with set included
    from app.schemas import DJSetResponse
    log_dict = LogResponse.model_validate(new_log).model_dump()
    if new_log.set:
        log_dict['set'] = DJSetResponse.model_validate(new_log.set).model_dump()
    
    return LogResponse(**log_dict)


@router.get("/users/{user_id}", response_model=PaginatedResponse)
async def get_user_logs(
    user_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    source_type: Optional[str] = Query(None, description="Filter by source type (youtube, soundcloud, live)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of sets logged by a user.
    
    Optionally filter by source_type (e.g., 'live' to get only live sets).
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Build query - join with DJSet to filter by source_type
    query = (
        select(UserSetLog)
        .join(DJSet, UserSetLog.set_id == DJSet.id)
        .where(UserSetLog.user_id == user_id)
    )
    
    # Filter by source_type if provided
    if source_type:
        try:
            source_enum = SourceType(source_type)
            query = query.where(DJSet.source_type == source_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source_type: {source_type}"
            )
    
    # Support filtering out live sets (for "listened" sets)
    # If source_type is not provided, we can add exclude_live parameter
    # For now, we'll handle this via source_type filter or frontend filtering
    
    query = query.order_by(UserSetLog.watched_date.desc())
    
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
    
    # Load set relationships and convert to response schemas
    from app.schemas import DJSetResponse
    log_responses = []
    for log in logs:
        await db.refresh(log, ["set"])
        log_dict = LogResponse.model_validate(log).model_dump()
        if log.set:
            log_dict['set'] = DJSetResponse.model_validate(log.set).model_dump()
        log_responses.append(LogResponse(**log_dict))
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    return PaginatedResponse(
        items=log_responses,
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
    await db.refresh(log_obj, ["set"])
    
    # Convert to response schema with set included
    from app.schemas import DJSetResponse
    log_dict = LogResponse.model_validate(log_obj).model_dump()
    if log_obj.set:
        log_dict['set'] = DJSetResponse.model_validate(log_obj.set).model_dump()
    
    return LogResponse(**log_dict)


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

