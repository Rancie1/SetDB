"""
Quick script to re-fetch oEmbed thumbnails for all SoundCloud sets.

This will get the original oEmbed thumbnail URLs (which are high quality)
without any modifications.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import DJSet, SourceType
import logging
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_thumbnail_urls():
    """Re-fetch oEmbed thumbnails for all SoundCloud sets."""
    async with AsyncSessionLocal() as db:
        # Find all SoundCloud sets
        result = await db.execute(
            select(DJSet).where(DJSet.source_type == SourceType.SOUNDCLOUD)
        )
        sets = result.scalars().all()
        
        logger.info(f"Found {len(sets)} SoundCloud sets to update")
        
        fixed_count = 0
        
        async with httpx.AsyncClient() as client:
            for set_obj in sets:
                try:
                    # Get oEmbed thumbnail
                    oembed_url = "https://soundcloud.com/oembed"
                    oembed_params = {"url": set_obj.source_url, "format": "json"}
                    
                    response = await client.get(
                        oembed_url,
                        params=oembed_params,
                        timeout=10.0,
                        follow_redirects=True
                    )
                    
                    if response.status_code == 200:
                        oembed_data = response.json()
                        oembed_thumbnail = oembed_data.get("thumbnail_url")
                        
                        if oembed_thumbnail and oembed_thumbnail != set_obj.thumbnail_url:
                            old_url = set_obj.thumbnail_url
                            set_obj.thumbnail_url = oembed_thumbnail
                            fixed_count += 1
                            logger.info(f"Updated: {set_obj.title}")
                            logger.info(f"  Old: {old_url[:60]}...")
                            logger.info(f"  New: {oembed_thumbnail[:60]}...")
                except Exception as e:
                    logger.warning(f"Failed to update {set_obj.title}: {str(e)}")
                    continue
        
        if fixed_count > 0:
            await db.commit()
            logger.info(f"\n✅ Updated {fixed_count} thumbnail URLs with oEmbed originals")
        else:
            logger.info("\n✅ No thumbnails needed updating")


if __name__ == "__main__":
    asyncio.run(fix_thumbnail_urls())
