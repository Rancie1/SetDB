"""
Backfill artists from existing Spotify tracks in the database.

Scans all tracks that have a spotify_track_id, fetches artist info
from the Spotify API, and creates Artist rows for any that don't exist.

Usage: python -m scripts.backfill_artists
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Track, Artist
from app.services.spotify_search import get_track_by_id, get_artists_batch


async def backfill():
    async with AsyncSessionLocal() as db:
        # Get all tracks with Spotify IDs
        result = await db.execute(
            select(Track).where(Track.spotify_track_id.isnot(None))
        )
        tracks = result.scalars().all()
        print(f"Found {len(tracks)} tracks with Spotify IDs")

        # Get existing artists
        existing_result = await db.execute(select(Artist.spotify_artist_id))
        existing_ids = {row[0] for row in existing_result.all()}
        print(f"Already have {len(existing_ids)} artists in DB")

        # Collect all unique Spotify artist IDs from track data
        # We need to fetch each track from Spotify to get artist IDs
        all_artist_ids = set()
        batch_size = 50
        track_ids = [t.spotify_track_id for t in tracks if t.spotify_track_id]

        print(f"Fetching artist IDs from {len(track_ids)} Spotify tracks...")
        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i:i + batch_size]
            for tid in batch:
                track_data = await get_track_by_id(tid)
                if track_data and track_data.get('artist_ids'):
                    for aid in track_data['artist_ids']:
                        if aid not in existing_ids:
                            all_artist_ids.add(aid)
            print(f"  Processed {min(i + batch_size, len(track_ids))}/{len(track_ids)} tracks, found {len(all_artist_ids)} new artist IDs")

        if not all_artist_ids:
            print("No new artists to create.")
            return

        # Fetch artist profiles in batches of 50
        artist_ids_list = list(all_artist_ids)
        created = 0
        for i in range(0, len(artist_ids_list), 50):
            batch = artist_ids_list[i:i + 50]
            artists_data = await get_artists_batch(batch)

            for sa in artists_data:
                # Double-check not already existing
                check = await db.execute(
                    select(Artist).where(Artist.spotify_artist_id == sa['spotify_artist_id'])
                )
                if check.scalar_one_or_none():
                    continue

                artist = Artist(
                    name=sa['name'],
                    spotify_artist_id=sa['spotify_artist_id'],
                    spotify_url=sa.get('spotify_url'),
                    image_url=sa.get('image_url'),
                    genres=sa.get('genres'),
                )
                db.add(artist)
                created += 1

            await db.commit()
            print(f"  Created {created} artists so far...")

        print(f"Done! Created {created} new artists.")


if __name__ == "__main__":
    asyncio.run(backfill())
