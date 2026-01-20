"""
Track search API routes.

Handles searching for tracks on SoundCloud.
"""

from fastapi import APIRouter, Depends, Query
from typing import List
from app.auth import get_current_active_user
from app.models import User
from app.services import soundcloud_search

router = APIRouter(prefix="/api/tracks", tags=["tracks"])


@router.get("/search/soundcloud", response_model=List[dict])
async def search_soundcloud(
    query: str = Query(..., min_length=1, description="Search query for tracks"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    current_user: User = Depends(get_current_active_user),
):
    """Search for tracks on SoundCloud."""
    results = await soundcloud_search.search_soundcloud_tracks(query, limit)
    return results
