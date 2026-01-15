"""
Script to clean up events that were migrated but still exist in dj_sets table.

This script finds any sets in dj_sets that have corresponding entries in the events table
(based on matching IDs) and removes them from dj_sets, since they should only exist in events.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import AsyncSessionLocal
from app.models import DJSet, Event
from sqlalchemy import select, delete


async def cleanup_events_from_sets():
    """Remove events from dj_sets table that exist in events table."""
    async with AsyncSessionLocal() as db:
        try:
            # Find all event IDs
            result = await db.execute(select(Event.id))
            event_ids = [row[0] for row in result.all()]
            
            if not event_ids:
                print("No events found in events table.")
                return
            
            print(f"Found {len(event_ids)} events in events table.")
            
            # Find sets in dj_sets that match event IDs
            result = await db.execute(
                select(DJSet.id, DJSet.title).where(DJSet.id.in_(event_ids))
            )
            sets_to_delete = result.all()
            
            if not sets_to_delete:
                print("No matching sets found in dj_sets table to delete.")
                return
            
            print(f"\nFound {len(sets_to_delete)} sets in dj_sets that should be removed:")
            for set_id, title in sets_to_delete:
                print(f"  - {set_id}: {title}")
            
            # Delete the sets
            await db.execute(
                delete(DJSet).where(DJSet.id.in_(event_ids))
            )
            await db.commit()
            
            print(f"\nSuccessfully deleted {len(sets_to_delete)} sets from dj_sets table.")
            print("These entries now only exist in the events table.")
            
        except Exception as e:
            await db.rollback()
            print(f"Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(cleanup_events_from_sets())
