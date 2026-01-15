"""
Script to update existing SoundCloud sets with high-quality thumbnails and full metadata.

This script:
1. Finds all SoundCloud sets that were imported with oEmbed (or missing metadata)
2. Re-fetches them using the full SoundCloud API
3. Updates thumbnails and metadata in the database

Run with: python -m scripts.update_soundcloud_sets
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine
from app.models import DJSet, SourceType
from app.services.soundcloud import fetch_soundcloud_track_info_api, fetch_soundcloud_track_info
import logging
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_soundcloud_sets(force_all=False):
    """
    Update all SoundCloud sets with high-quality thumbnails and full metadata.
    
    Args:
        force_all: If True, update all sets regardless of current state
    """
    async with AsyncSessionLocal() as db:
        # Find all SoundCloud sets
        result = await db.execute(
            select(DJSet).where(DJSet.source_type == SourceType.SOUNDCLOUD)
        )
        sets = result.scalars().all()
        
        logger.info(f"Found {len(sets)} SoundCloud sets to check")
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for set_obj in sets:
            try:
                # Check if this set needs updating
                # Update if: using oEmbed source, missing duration, missing published_at, or low-quality thumbnail
                metadata = set_obj.extra_metadata or {}
                source = metadata.get("source", "")
                
                # Check thumbnail quality - update if it's low quality (-t500x500, -t200x200, etc.)
                has_low_quality_thumbnail = False
                if set_obj.thumbnail_url:
                    # Check for low-quality size suffixes
                    import re
                    if re.search(r'-[a-z]\d+x\d+\.(jpg|png)$', set_obj.thumbnail_url):
                        has_low_quality_thumbnail = True
                    # Also update if it's -original.jpg (we want -large.jpg which is more reliable)
                    elif '-original.' in set_obj.thumbnail_url:
                        has_low_quality_thumbnail = True
                
                needs_update = force_all or (
                    source == "oembed" or
                    source == "unknown" or
                    set_obj.duration_minutes is None or
                    "published_at" not in metadata or
                    has_low_quality_thumbnail
                )
                
                if not needs_update:
                    logger.debug(f"Skipping {set_obj.title} - already has full metadata")
                    skipped_count += 1
                    continue
                
                # Log why we're updating
                reasons = []
                if force_all:
                    reasons.append("force update")
                if source == "oembed":
                    reasons.append("oembed source")
                if source == "unknown":
                    reasons.append("unknown source")
                if set_obj.duration_minutes is None:
                    reasons.append("missing duration")
                if "published_at" not in metadata:
                    reasons.append("missing published_at")
                if has_low_quality_thumbnail:
                    reasons.append("low-quality thumbnail")
                logger.info(f"Update reasons: {', '.join(reasons)}")
                
                logger.info(f"Updating: {set_obj.title} ({set_obj.source_url})")
                
                # Try to get API data first (for full metadata)
                # We'll try multiple times if needed
                api_info = None
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        api_info = await fetch_soundcloud_track_info_api(set_obj.source_url)
                        if api_info:
                            logger.info(f"  ✓ Got API data for {set_obj.title} (attempt {attempt + 1})")
                            break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"  ⚠ API call failed for {set_obj.title} (attempt {attempt + 1}), retrying...")
                            await asyncio.sleep(1)  # Wait 1 second before retry
                        else:
                            logger.warning(f"  ⚠ API call failed for {set_obj.title} after {max_retries} attempts: {str(e)}")
                            logger.warning(f"  This set will have limited metadata (no published_at, etc.)")
                
                # Get oEmbed thumbnail separately (for high quality)
                oembed_thumbnail = None
                try:
                    oembed_url = "https://soundcloud.com/oembed"
                    oembed_params = {"url": set_obj.source_url, "format": "json"}
                    async with httpx.AsyncClient() as oembed_client:
                        oembed_response = await oembed_client.get(
                            oembed_url,
                            params=oembed_params,
                            timeout=10.0,
                            follow_redirects=True
                        )
                        if oembed_response.status_code == 200:
                            oembed_data = oembed_response.json()
                            oembed_thumbnail = oembed_data.get("thumbnail_url")
                            # Use oEmbed thumbnail as-is (oEmbed returns good quality)
                            # Don't modify the URL - oEmbed provides optimized, high-quality images
                            if oembed_thumbnail:
                                logger.debug(f"  Got oEmbed thumbnail: {oembed_thumbnail}")
                except Exception as e:
                    logger.warning(f"  ⚠ Could not get oEmbed thumbnail: {str(e)}")
                
                # Build track_info from API data if available, otherwise use oEmbed fallback
                if api_info:
                    # Use API data as base
                    track_info = {
                        "title": api_info.get("title", ""),
                        "description": api_info.get("description", ""),
                        "dj_name": api_info.get("dj_name", ""),
                        "duration_minutes": api_info.get("duration_minutes"),
                        "created_at": api_info.get("created_at"),
                        "thumbnail_url": oembed_thumbnail or api_info.get("thumbnail_url"),  # Prefer oEmbed thumbnail
                        "metadata": api_info.get("metadata", {}).copy()  # Make a copy to avoid mutating original
                    }
                    # Ensure source is marked as "api" and all metadata is present
                    track_info["metadata"]["source"] = "api"
                    logger.info(f"  ✓ Built track_info from API data with oEmbed thumbnail")
                    logger.debug(f"  API created_at: {api_info.get('created_at')}")
                    logger.debug(f"  API duration: {api_info.get('duration_minutes')}")
                    logger.debug(f"  Track info metadata keys: {list(track_info.get('metadata', {}).keys())}")
                else:
                    # API failed - use oEmbed fallback
                    logger.warning(f"  ⚠ Could not get API data for: {set_obj.source_url}")
                    logger.warning(f"  This might be due to: invalid URL, private track, or API rate limiting")
                    track_info = await fetch_soundcloud_track_info(set_obj.source_url)
                    # Upgrade oEmbed thumbnail if we got one
                    if track_info.get("thumbnail_url") and oembed_thumbnail:
                        track_info["thumbnail_url"] = oembed_thumbnail
                
                # Check if we got API data - if api_info exists, we definitely got API data
                got_api_data = api_info is not None
                
                # Update the set with new information
                if track_info.get("thumbnail_url"):
                    set_obj.thumbnail_url = track_info["thumbnail_url"]
                
                if track_info.get("duration_minutes") is not None:
                    set_obj.duration_minutes = track_info["duration_minutes"]
                
                # Update metadata - replace entirely to ensure clean state
                new_metadata = track_info.get("metadata", {}).copy() if track_info.get("metadata") else {}
                
                # Add published_at if available from API
                if track_info.get("created_at"):
                    new_metadata["published_at"] = track_info["created_at"]
                
                # Ensure source is set correctly
                if api_info:
                    # We got API data, mark as "api"
                    new_metadata["source"] = "api"
                    logger.debug(f"  Setting source to 'api' (got API data)")
                elif track_info.get("metadata", {}).get("source"):
                    # Use source from track_info
                    new_metadata["source"] = track_info["metadata"]["source"]
                else:
                    # Fallback
                    new_metadata["source"] = "oembed"
                
                # Replace metadata entirely (don't merge, to avoid old data)
                set_obj.extra_metadata = new_metadata
                
                logger.debug(f"  Final metadata source: {set_obj.extra_metadata.get('source')}")
                logger.debug(f"  Final metadata has published_at: {'published_at' in set_obj.extra_metadata}")
                
                # Refresh the updated_at timestamp
                from datetime import datetime
                set_obj.updated_at = datetime.utcnow()
                
                await db.commit()
                await db.refresh(set_obj)  # Refresh to ensure changes are loaded
                
                updated_count += 1
                logger.info(f"✅ Updated: {set_obj.title}")
                logger.info(f"   Thumbnail: {set_obj.thumbnail_url}")
                logger.info(f"   Duration: {set_obj.duration_minutes} min")
                logger.info(f"   Source: {set_obj.extra_metadata.get('source', 'unknown')}")
                
            except Exception as e:
                import traceback
                logger.error(f"❌ Error updating {set_obj.title}: {str(e)}")
                logger.debug(f"Full traceback: {traceback.format_exc()}")
                error_count += 1
                await db.rollback()
                continue
        
        logger.info("\n" + "="*50)
        logger.info(f"Update complete!")
        logger.info(f"  ✅ Updated: {updated_count}")
        logger.info(f"  ⏭️  Skipped: {skipped_count}")
        logger.info(f"  ❌ Errors: {error_count}")
        logger.info("="*50)


if __name__ == "__main__":
    import sys
    force_all = "--force" in sys.argv or "-f" in sys.argv
    if force_all:
        logger.info("Running in FORCE mode - will update all sets")
    asyncio.run(update_soundcloud_sets(force_all=force_all))
