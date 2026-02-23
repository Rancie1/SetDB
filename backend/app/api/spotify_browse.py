"""
Spotify Browse API routes.

Provides endpoints for browsing Spotify's catalog: genres, recommendations,
new releases, and artist top tracks.
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional, List
import logging

from app.services.spotify_search import (
    get_genre_seeds,
    get_recommendations,
    get_new_releases,
    get_artist_top_tracks,
    get_track_by_id,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/spotify/browse", tags=["spotify-browse"])


@router.get("/genres")
async def browse_genres():
    """Get available genre seeds for browsing and recommendations."""
    genres = await get_genre_seeds()
    return {"genres": genres}


@router.get("/recommendations")
async def browse_recommendations(
    seed_tracks: Optional[str] = Query(None, description="Comma-separated Spotify track IDs (max 5)"),
    seed_artists: Optional[str] = Query(None, description="Comma-separated Spotify artist IDs (max 5)"),
    seed_genres: Optional[str] = Query(None, description="Comma-separated genre names (max 5)"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Get track recommendations based on seed tracks, artists, or genres.
    
    At least one seed parameter is required. Combined seeds cannot exceed 5.
    """
    tracks_list = [t.strip() for t in seed_tracks.split(",") if t.strip()] if seed_tracks else None
    artists_list = [a.strip() for a in seed_artists.split(",") if a.strip()] if seed_artists else None
    genres_list = [g.strip() for g in seed_genres.split(",") if g.strip()] if seed_genres else None
    
    if not tracks_list and not artists_list and not genres_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one seed (seed_tracks, seed_artists, or seed_genres) is required.",
        )
    
    tracks = await get_recommendations(
        seed_tracks=tracks_list,
        seed_artists=artists_list,
        seed_genres=genres_list,
        limit=limit,
    )
    return {"tracks": tracks}


@router.get("/new-releases")
async def browse_new_releases(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    """Get new album releases."""
    data = await get_new_releases(limit=limit, offset=offset)
    return data


@router.get("/artist/{artist_id}/top-tracks")
async def browse_artist_top_tracks(artist_id: str):
    """Get top tracks for a Spotify artist."""
    tracks = await get_artist_top_tracks(artist_id)
    if not tracks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found or no top tracks available.",
        )
    return {"tracks": tracks}


@router.get("/track/{track_id}")
async def browse_track(track_id: str):
    """Get a single track's details from Spotify (for previewing before adding to DB)."""
    track = await get_track_by_id(track_id)
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found on Spotify.",
        )
    return track
