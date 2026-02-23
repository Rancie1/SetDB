"""
Artist API routes.

Handles artist profile viewing and editing.
Artists are auto-created from Spotify data when tracks are imported.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from uuid import UUID
from typing import Optional, List

from app.database import get_db
from app.models import Artist, Track, DJSet, Event, User
from app.schemas import ArtistResponse, ArtistDetailResponse, ArtistUpdate, TrackResponse, DJSetResponse, EventResponse
from app.auth import get_current_active_user

router = APIRouter(prefix="/api/artists", tags=["artists"])

security = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    if not credentials:
        return None
    try:
        from jose import jwt
        from app.config import settings
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            return None
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        return result.scalar_one_or_none()
    except Exception:
        return None


@router.get("", response_model=List[ArtistResponse])
async def list_artists(
    query: Optional[str] = Query(None, min_length=1, description="Search by artist name"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List artists with optional name search."""
    q = select(Artist)
    if query:
        q = q.where(func.lower(Artist.name).contains(query.lower()))
    q = q.order_by(Artist.name).offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    artists = result.scalars().all()
    return [ArtistResponse.model_validate(a) for a in artists]


@router.get("/by-name/{name}", response_model=ArtistResponse)
async def get_artist_by_name(
    name: str,
    db: AsyncSession = Depends(get_db),
):
    """Look up an artist by name. Returns 404 if not found."""
    result = await db.execute(
        select(Artist).where(func.lower(Artist.name) == name.lower())
    )
    artist = result.scalar_one_or_none()
    if not artist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found")
    return ArtistResponse.model_validate(artist)


@router.get("/{artist_id}", response_model=ArtistDetailResponse)
async def get_artist_detail(
    artist_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get artist profile with aggregated tracks, sets, and events."""
    result = await db.execute(select(Artist).where(Artist.id == artist_id))
    artist = result.scalar_one_or_none()
    if not artist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found")

    name_lower = artist.name.lower()

    # Tracks where artist_name contains this artist
    tracks_result = await db.execute(
        select(Track)
        .where(func.lower(Track.artist_name).contains(name_lower))
        .order_by(Track.created_at.desc())
        .limit(50)
    )
    tracks = [TrackResponse.model_validate(t).model_dump() for t in tracks_result.scalars().all()]

    # Sets where dj_name or title contains this artist
    sets_result = await db.execute(
        select(DJSet)
        .where(
            or_(
                func.lower(DJSet.dj_name).contains(name_lower),
                func.lower(DJSet.title).contains(name_lower),
            )
        )
        .order_by(DJSet.created_at.desc())
        .limit(50)
    )
    sets = [DJSetResponse.model_validate(s).model_dump() for s in sets_result.scalars().all()]

    # Events where dj_name contains this artist
    events = []
    try:
        events_result = await db.execute(
            select(Event)
            .where(func.lower(Event.dj_name).contains(name_lower))
            .order_by(Event.created_at.desc())
            .limit(50)
        )
        events = [EventResponse.model_validate(e).model_dump() for e in events_result.scalars().all()]
    except Exception:
        pass

    artist_dict = ArtistResponse.model_validate(artist).model_dump()
    artist_dict["tracks"] = tracks
    artist_dict["sets"] = sets
    artist_dict["events"] = events

    return ArtistDetailResponse(**artist_dict)


@router.put("/{artist_id}", response_model=ArtistResponse)
async def update_artist(
    artist_id: UUID,
    update_data: ArtistUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user-editable artist fields (bio, social links)."""
    result = await db.execute(select(Artist).where(Artist.id == artist_id))
    artist = result.scalar_one_or_none()
    if not artist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(artist, field, value)

    await db.commit()
    await db.refresh(artist)
    return ArtistResponse.model_validate(artist)


async def ensure_artists_from_spotify(
    artist_ids: List[str],
    db: AsyncSession,
) -> List[Artist]:
    """
    Given a list of Spotify artist IDs, ensure each has an Artist row.
    Fetches missing artists from Spotify API and creates them.
    Returns the list of Artist objects.
    """
    if not artist_ids:
        return []

    # Find which already exist
    existing_result = await db.execute(
        select(Artist).where(Artist.spotify_artist_id.in_(artist_ids))
    )
    existing = {a.spotify_artist_id: a for a in existing_result.scalars().all()}

    missing_ids = [aid for aid in artist_ids if aid not in existing]
    if not missing_ids:
        return list(existing.values())

    # Fetch missing from Spotify
    from app.services.spotify_search import get_artists_batch
    spotify_artists = await get_artists_batch(missing_ids)

    new_artists = []
    for sa in spotify_artists:
        if sa["spotify_artist_id"] in existing:
            continue
        artist = Artist(
            name=sa["name"],
            spotify_artist_id=sa["spotify_artist_id"],
            spotify_url=sa.get("spotify_url"),
            image_url=sa.get("image_url"),
            genres=sa.get("genres"),
        )
        db.add(artist)
        new_artists.append(artist)
        existing[sa["spotify_artist_id"]] = artist

    if new_artists:
        await db.flush()

    return list(existing.values())
