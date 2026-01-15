"""
Script to check which sets can be marked as live and diagnose issues.

This helps identify why older sets might not be markable as live.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import AsyncSessionLocal
from app.models import DJSet, User
from app.models import SourceType
from sqlalchemy import select


async def check_sets_for_live_marking():
    """Check sets and identify which can/cannot be marked as live."""
    async with AsyncSessionLocal() as db:
        try:
            # Get all sets
            result = await db.execute(select(DJSet))
            all_sets = result.scalars().all()
            
            print(f"Total sets in database: {len(all_sets)}\n")
            
            # Categorize sets
            can_mark_as_live = []
            cannot_mark_as_live = []
            
            for set_obj in all_sets:
                issues = []
                
                # Check source_type
                if set_obj.source_type == SourceType.LIVE:
                    issues.append("Already a live set")
                elif set_obj.source_type not in [SourceType.YOUTUBE, SourceType.SOUNDCLOUD]:
                    issues.append(f"Invalid source_type: {set_obj.source_type} (must be youtube or soundcloud)")
                
                # Check if set has required fields
                if not set_obj.source_url:
                    issues.append("Missing source_url")
                
                if issues:
                    cannot_mark_as_live.append({
                        'id': str(set_obj.id),
                        'title': set_obj.title,
                        'dj_name': set_obj.dj_name,
                        'source_type': set_obj.source_type.value if hasattr(set_obj.source_type, 'value') else str(set_obj.source_type),
                        'created_at': set_obj.created_at,
                        'created_by_id': str(set_obj.created_by_id),
                        'issues': issues
                    })
                else:
                    can_mark_as_live.append({
                        'id': str(set_obj.id),
                        'title': set_obj.title,
                        'dj_name': set_obj.dj_name,
                        'source_type': set_obj.source_type.value if hasattr(set_obj.source_type, 'value') else str(set_obj.source_type),
                        'created_at': set_obj.created_at,
                        'created_by_id': str(set_obj.created_by_id)
                    })
            
            print(f"✅ Sets that CAN be marked as live: {len(can_mark_as_live)}")
            print(f"❌ Sets that CANNOT be marked as live: {len(cannot_mark_as_live)}\n")
            
            if cannot_mark_as_live:
                print("=" * 80)
                print("SETS THAT CANNOT BE MARKED AS LIVE:")
                print("=" * 80)
                for set_info in cannot_mark_as_live:
                    print(f"\nID: {set_info['id']}")
                    print(f"Title: {set_info['title']}")
                    print(f"DJ: {set_info['dj_name']}")
                    print(f"Source Type: {set_info['source_type']}")
                    print(f"Created: {set_info['created_at']}")
                    print(f"Created By: {set_info['created_by_id']}")
                    print("Issues:")
                    for issue in set_info['issues']:
                        print(f"  - {issue}")
                    print("-" * 80)
            
            # Show summary by source_type
            print("\n" + "=" * 80)
            print("SUMMARY BY SOURCE TYPE:")
            print("=" * 80)
            source_type_counts = {}
            for set_obj in all_sets:
                source_type = set_obj.source_type.value if hasattr(set_obj.source_type, 'value') else str(set_obj.source_type)
                source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
            
            for source_type, count in sorted(source_type_counts.items()):
                print(f"{source_type}: {count}")
            
            # Show sets by creation date (to identify old sets)
            print("\n" + "=" * 80)
            print("OLDEST SETS (first 10):")
            print("=" * 80)
            sorted_sets = sorted(all_sets, key=lambda s: s.created_at)
            for set_obj in sorted_sets[:10]:
                source_type = set_obj.source_type.value if hasattr(set_obj.source_type, 'value') else str(set_obj.source_type)
                print(f"{set_obj.created_at.strftime('%Y-%m-%d')} | {source_type:12} | {set_obj.title[:50]}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    asyncio.run(check_sets_for_live_marking())
