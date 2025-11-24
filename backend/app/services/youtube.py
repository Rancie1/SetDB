"""
YouTube API integration service.

Handles fetching video information from YouTube Data API v3.
"""

import re
import httpx
from typing import Optional, Dict
from app.config import settings


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats.
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://youtube.com/watch?v=VIDEO_ID
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def parse_duration(duration_str: str) -> Optional[int]:
    """
    Parse ISO 8601 duration format to minutes.
    
    Example: "PT1H23M45S" -> 83 (minutes)
    """
    if not duration_str:
        return None
    
    # Remove PT prefix
    duration_str = duration_str.replace("PT", "")
    
    hours = 0
    minutes = 0
    seconds = 0
    
    # Extract hours
    hour_match = re.search(r'(\d+)H', duration_str)
    if hour_match:
        hours = int(hour_match.group(1))
    
    # Extract minutes
    minute_match = re.search(r'(\d+)M', duration_str)
    if minute_match:
        minutes = int(minute_match.group(1))
    
    # Extract seconds
    second_match = re.search(r'(\d+)S', duration_str)
    if second_match:
        seconds = int(second_match.group(1))
    
    # Convert to total minutes
    total_minutes = hours * 60 + minutes + (seconds / 60)
    return int(total_minutes)


async def fetch_youtube_video_info(video_id: str) -> Dict:
    """
    Fetch video information from YouTube Data API v3.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Dictionary with video information
        
    Raises:
        Exception: If API call fails or video not found
    """
    if not settings.YOUTUBE_API_KEY:
        raise Exception("YouTube API key not configured")
    
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "id": video_id,
        "key": settings.YOUTUBE_API_KEY,
        "part": "snippet,contentDetails"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("items"):
            raise Exception(f"YouTube video {video_id} not found")
        
        item = data["items"][0]
        snippet = item["snippet"]
        content_details = item.get("contentDetails", {})
        
        # Extract information
        title = snippet.get("title", "")
        description = snippet.get("description", "")
        thumbnail_url = snippet.get("thumbnails", {}).get("high", {}).get("url") or \
                        snippet.get("thumbnails", {}).get("medium", {}).get("url") or \
                        snippet.get("thumbnails", {}).get("default", {}).get("url")
        channel_name = snippet.get("channelTitle", "")
        duration_str = content_details.get("duration", "")
        duration_minutes = parse_duration(duration_str)
        
        return {
            "title": title,
            "description": description,
            "thumbnail_url": thumbnail_url,
            "dj_name": channel_name,  # Use channel name as DJ name
            "duration_minutes": duration_minutes,
            "metadata": {
                "channel_id": snippet.get("channelId"),
                "published_at": snippet.get("publishedAt"),
                "video_id": video_id
            }
        }


async def import_from_youtube_url(url: str) -> Dict:
    """
    Import DJ set information from YouTube URL.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Dictionary with set information ready for database
        
    Raises:
        Exception: If URL is invalid or API call fails
    """
    video_id = extract_video_id(url)
    
    if not video_id:
        raise Exception("Invalid YouTube URL format")
    
    video_info = await fetch_youtube_video_info(video_id)
    
    return {
        "title": video_info["title"],
        "dj_name": video_info["dj_name"],
        "source_type": "youtube",
        "source_id": video_id,
        "source_url": url,
        "description": video_info["description"],
        "thumbnail_url": video_info["thumbnail_url"],
        "duration_minutes": video_info["duration_minutes"],
        "metadata": video_info["metadata"]
    }

