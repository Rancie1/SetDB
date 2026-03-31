"""
Ticketmaster Discovery API service.

Uses Ticketmaster Discovery API v2 for mainstream festival and large show data.
Requires TICKETMASTER_API_KEY in environment.
"""

import httpx
from typing import Optional
from datetime import date

TM_BASE_URL = "https://app.ticketmaster.com/discovery/v2"


async def search_events(
    api_key: str,
    keyword: Optional[str] = None,
    city: Optional[str] = None,
    country_code: Optional[str] = None,
    page: int = 0,
    limit: int = 20,
) -> dict:
    """Search Ticketmaster events filtered to electronic/music genre."""
    params = {
        "apikey": api_key,
        "classificationName": "music",
        "size": limit,
        "page": page,
    }
    if keyword:
        params["keyword"] = keyword
    if city:
        params["city"] = city
    if country_code:
        params["countryCode"] = country_code

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(f"{TM_BASE_URL}/events.json", params=params)
        response.raise_for_status()
        data = response.json()

    embedded = data.get("_embedded", {})
    raw_events = embedded.get("events", [])
    page_info = data.get("page", {})
    total = page_info.get("totalElements", 0)

    return {
        "results": [parse_ticketmaster_event(e) for e in raw_events],
        "total": total,
        "page": page,
        "page_size": limit,
    }


async def fetch_event(api_key: str, tm_id: str) -> dict:
    """Fetch a single Ticketmaster event by ID."""
    params = {"apikey": api_key}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(f"{TM_BASE_URL}/events/{tm_id}.json", params=params)
        response.raise_for_status()
        data = response.json()

    return parse_ticketmaster_event(data)


def parse_ticketmaster_event(raw: dict) -> dict:
    """Convert a raw Ticketmaster event dict to an EventCreate-compatible dict."""
    # Venue
    embedded = raw.get("_embedded", {})
    venues = embedded.get("venues", [])
    venue = venues[0] if venues else {}
    venue_name = venue.get("name", "")
    city = (venue.get("city") or {}).get("name", "")
    country = (venue.get("country") or {}).get("name", "")
    venue_parts = [p for p in [venue_name, city, country] if p]
    venue_location = ", ".join(venue_parts) if venue_parts else None

    # Artists / attractions
    attractions = embedded.get("attractions", [])
    artist_names = ", ".join(a["name"] for a in attractions if a.get("name"))

    # Thumbnail
    images = raw.get("images", [])
    # Prefer wider aspect ratio images
    thumbnail = next(
        (img["url"] for img in images if img.get("ratio") == "16_9" and img.get("width", 0) >= 640),
        images[0]["url"] if images else None,
    )

    # Date
    dates = raw.get("dates", {})
    start = dates.get("start", {})
    local_date = start.get("localDate")
    event_date = None
    if local_date:
        try:
            from datetime import date as date_cls
            event_date = date_cls.fromisoformat(local_date)
        except Exception:
            pass

    # Ticket URL
    ticket_url = raw.get("url")

    title = raw.get("name", "Unknown Event")

    return {
        "title": f"{artist_names} at {venue_name}" if artist_names and venue_name else title,
        "dj_name": artist_names or title,
        "event_name": title,
        "event_date": event_date,
        "venue_location": venue_location,
        "thumbnail_url": thumbnail,
        "description": None,
        "ticket_url": ticket_url,
        "external_id": f"tm_{raw['id']}",
    }
