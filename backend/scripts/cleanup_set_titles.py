"""
Script to clean up set titles by removing " by Artist Name" from existing sets.

This removes the " by Artist Name" suffix from titles where the artist name
is already stored in the dj_name field.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import AsyncSessionLocal
from app.models import DJSet
from sqlalchemy import select, update


async def cleanup_set_titles():
    """Remove ' by Artist Name' from set titles."""
    async with AsyncSessionLocal() as db:
        try:
            # Get all sets
            result = await db.execute(select(DJSet))
            all_sets = result.scalars().all()
            
            print(f"Total sets in database: {len(all_sets)}\n")
            
            sets_to_update = []
            
            for set_obj in all_sets:
                if " by " in set_obj.title:
                    # Split on " by " and take the first part
                    parts = set_obj.title.split(" by ", 1)
                    if len(parts) > 1:
                        new_title = parts[0].strip()
                        if new_title != set_obj.title:
                            sets_to_update.append({
                                'id': set_obj.id,
                                'old_title': set_obj.title,
                                'new_title': new_title,
                                'dj_name': set_obj.dj_name
                            })
            
            if not sets_to_update:
                print("No sets need title cleanup.")
                return
            
            print(f"Found {len(sets_to_update)} sets with ' by Artist Name' in title:\n")
            for item in sets_to_update:
                print(f"  - {item['old_title']}")
                print(f"    → {item['new_title']}")
                print(f"    DJ: {item['dj_name']}\n")
            
            # Ask for confirmation
            response = input(f"\nUpdate {len(sets_to_update)} sets? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled.")
                return
            
            # Update sets
            updated_count = 0
            for item in sets_to_update:
                await db.execute(
                    update(DJSet)
                    .where(DJSet.id == item['id'])
                    .values(title=item['new_title'])
                )
                updated_count += 1
            
            await db.commit()
            
            print(f"\n✅ Successfully updated {updated_count} sets.")
            
        except Exception as e:
            await db.rollback()
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    asyncio.run(cleanup_set_titles())
