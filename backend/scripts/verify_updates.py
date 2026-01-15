"""
Quick script to verify SoundCloud sets were updated correctly.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import DJSet, SourceType

async def verify_updates():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(DJSet).where(DJSet.source_type == SourceType.SOUNDCLOUD)
        )
        sets = result.scalars().all()
        
        print(f"\nFound {len(sets)} SoundCloud sets:\n")
        print("=" * 80)
        
        for s in sets:
            metadata = s.extra_metadata or {}
            source = metadata.get("source", "unknown")
            has_duration = s.duration_minutes is not None
            has_published = "published_at" in metadata
            
            print(f"Title: {s.title}")
            print(f"  Thumbnail: {s.thumbnail_url[:60] if s.thumbnail_url else 'None'}...")
            print(f"  Duration: {s.duration_minutes} min" if has_duration else "  Duration: None")
            print(f"  Source: {source}")
            print(f"  Has published_at: {has_published}")
            print("-" * 80)

if __name__ == "__main__":
    asyncio.run(verify_updates())
