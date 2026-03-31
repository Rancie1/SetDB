"""
Skiddle Events API service.

Uses Skiddle Events Search API for UK/EU club nights and venues.
Requires SKIDDLE_API_KEY in environment.
"""

import httpx
from typing import Optional
from datetime import date

SKIDDLE_BASE_URL = "https://www.skiddle.com/api/v1/events/search/"
SKIDDLE_EVENT_URL = "https://www.skiddle.com/api/v1/events/{id}/"


async def search_events(
    api_key: str,
    keyword: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius: int = 10,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Search Skiddle club night events."""
    params = {
        "api_key": api_key,
        "eventcode": "CLUB",
        "limit": limit,
        "offset": offset,
        "order": "date",
    }
    if keyword:
        params["keyword"] = keyword
    if latitude is not None:
        params["latitude"] = latitude
    if longitude is not None:
        params["longitude"] = longitude
        params["radius"] = radius
    if date_from:
        params["minDate"] = date_from.isoformat()
    if date_to:
        params["maxDate"] = date_to.isoformat()

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(SKIDDLE_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

    raw_events = data.get("results", [])
    total = data.get("totalcount", 0)

    return {
        "results": [parse_skiddle_event(e) for e in raw_events],
        "total": int(total) if total else 0,
        "page_size": limit,
        "offset": offset,
    }


async def fetch_event(api_key: str, skiddle_id: str) -> dict:
    """Fetch a single Skiddle event by ID."""
    params = {"api_key": api_key}
    url = SKIDDLE_EVENT_URL.format(id=skiddle_id)

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    result = data.get("results") or data
    return parse_skiddle_event(result)


def parse_skiddle_event(raw: dict) -> dict:
    """Convert a raw Skiddle event dict to an EventCreate-compatible dict."""
    venue = raw.get("venue") or {}
    venue_name = venue.get("name") or raw.get("venuename", "")
    town = venue.get("town") or raw.get("town", "")
    venue_parts = [p for p in [venue_name, town] if p]
    venue_location = ", ".join(venue_parts) if venue_parts else None

    # Artists / lineup
    artists = raw.get("artists") or []
    if isinstance(artists, list):
        artist_names = ", ".join(
            a.get("name", "") for a in artists if isinstance(a, dict) and a.get("name")
        )
    else:
        artist_names = ""

    # Thumbnail
    thumbnail_url = raw.get("largeimageurls") and raw["largeimageurls"][0] or raw.get("imageurl")

    # Date
    event_date = None
    date_str = raw.get("date") or raw.get("startdate")
    if date_str:
        try:
            from datetime import date as date_cls
            event_date = date_cls.fromisoformat(str(date_str)[:10])
        except Exception:
            pass

    event_name = raw.get("eventname") or raw.get("name") or "Unknown Event"
    ticket_url = raw.get("link") or raw.get("ticketsavailable")

    return {
        "title": f"{artist_names} at {venue_name}" if artist_names and venue_name else event_name,
        "dj_name": artist_names or "Unknown",
        "event_name": event_name,
        "event_date": event_date,
        "venue_location": venue_location,
        "thumbnail_url": thumbnail_url,
        "description": raw.get("description"),
        "ticket_url": ticket_url if isinstance(ticket_url, str) else None,
        "external_id": f"skiddle_{raw['id']}",
    }
