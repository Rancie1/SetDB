"""
Resident Advisor (RA) service.

Uses RA's internal GraphQL API for public event listings.
No API key required for public data.
"""

import httpx
from typing import Optional
from datetime import date

RA_GRAPHQL_URL = "https://ra.co/graphql"

_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://ra.co/",
    "Origin": "https://ra.co",
}

_EVENTS_QUERY = """
query GET_EVENTS($filters: FilterInputDtoInput, $pageSize: Int, $page: Int) {
  eventListings(filters: $filters, pageSize: $pageSize, page: $page) {
    data {
      id
      event {
        id
        title
        startTime
        endTime
        contentUrl
        flyerFront
        lineup
        venue {
          name
          area {
            name
            country {
              name
            }
          }
        }
        artists {
          name
        }
        images {
          filename
        }
      }
    }
    totalResults
  }
}
"""

_SINGLE_EVENT_QUERY = """
query GET_EVENT($id: ID!) {
  event(id: $id) {
    id
    title
    startTime
    endTime
    contentUrl
    flyerFront
    lineup
    venue {
      name
      area {
        name
        country {
          name
        }
      }
    }
    artists {
      name
    }
    images {
      filename
    }
  }
}
"""

_AREA_SEARCH_QUERY = """
query SEARCH_AREAS($searchTerm: String, $limit: Int) {
  areas(searchTerm: $searchTerm, limit: $limit) {
    id
    name
  }
}
"""



async def area_ids_for_name(city: str) -> list[int]:
    """Resolve a city name to a list of RA area integer IDs (up to 5)."""
    payload = {
        "query": _AREA_SEARCH_QUERY,
        "variables": {"searchTerm": city, "limit": 5},
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(RA_GRAPHQL_URL, json=payload, headers=_HEADERS)
        response.raise_for_status()
        data = response.json()

    areas = data.get("data", {}).get("areas") or []
    return [int(a["id"]) for a in areas if a.get("id")]


async def area_id_for_name(city: str) -> Optional[int]:
    """Resolve a city name to an RA area integer ID (first match only)."""
    ids = await area_ids_for_name(city)
    return ids[0] if ids else None


import asyncio
import re as _re

_STOP_WORDS = {"and", "the", "at", "in", "of", "a", "an", "&", "for", "with"}


def _keyword_words(keyword: str) -> list:
    """Split a keyword into significant words for matching."""
    return [
        w for w in keyword.lower().split()
        if w not in _STOP_WORDS
        and len(w) > 1
        and not _re.match(r"^\d{4}$", w)
    ]


def _keyword_matches(r: dict, words: list) -> bool:
    combined = " ".join([
        r.get("title") or "",
        r.get("dj_name") or "",
        r.get("event_name") or "",
        r.get("venue_location") or "",
    ]).lower()
    return all(w in combined for w in words)


async def _fetch_listings(filters: dict, pages_to_fetch: int, fetch_from_start: bool) -> list:
    """Fetch raw parsed events from RA for the given filters."""
    fetch_size = 100

    async with httpx.AsyncClient(timeout=20.0) as client:
        count_resp = await client.post(
            RA_GRAPHQL_URL,
            json={"query": _EVENTS_QUERY, "variables": {"filters": filters, "pageSize": 1, "page": 1}},
            headers=_HEADERS,
        )
        count_resp.raise_for_status()
        total_results = (
            count_resp.json().get("data", {}).get("eventListings", {}).get("totalResults", 0)
        ) or 0

        last_page = max(1, -(-total_results // fetch_size))
        if fetch_from_start:
            target_pages = list(range(1, min(pages_to_fetch + 1, last_page + 1)))
        else:
            target_pages = list(range(max(1, last_page - pages_to_fetch + 1), last_page + 1))

        async def fetch_page(p):
            resp = await client.post(
                RA_GRAPHQL_URL,
                json={"query": _EVENTS_QUERY, "variables": {"filters": filters, "pageSize": fetch_size, "page": p}},
                headers=_HEADERS,
            )
            resp.raise_for_status()
            return resp.json()

        pages_data = await asyncio.gather(*[fetch_page(p) for p in target_pages])

    seen_event_ids: set = set()
    results = []
    for data in pages_data:
        for listing in data.get("data", {}).get("eventListings", {}).get("data", []):
            event = listing.get("event")
            if not event:
                continue
            node_id = event.get("id")
            if node_id and node_id in seen_event_ids:
                continue
            if node_id:
                seen_event_ids.add(node_id)
            event["_listing_id"] = listing.get("id")
            results.append(parse_ra_event(event))

    return results


async def search_events(
    location: str,
    keyword: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Search RA events by location (city name) and optional keyword/date range."""
    from datetime import timedelta
    today = date.today()

    # ── date window ──────────────────────────────────────────────────────────
    if keyword:
        effective_from = date_from or (today - timedelta(days=548))  # ~18 months back
        effective_to   = date_to   or (today + timedelta(days=365))  # 1 year ahead
        pages_to_fetch = 20
        fetch_from_start = True
    else:
        effective_from = date_from or (today - timedelta(days=730))
        effective_to   = date_to   or today
        pages_to_fetch = 1
        fetch_from_start = False

    date_filter = {
        "listingDate": {
            "gte": f"{effective_from.isoformat()}T00:00:00",
            "lte": f"{effective_to.isoformat()}T23:59:59",
        }
    }

    # ── city-scoped search (all matching areas in parallel) ──────────────────
    area_ids = await area_ids_for_name(location)
    words = _keyword_words(keyword) if keyword else []

    results: list = []
    if area_ids:
        # Fetch each area in parallel and merge, deduplicating by ra_event_id
        area_batches = await asyncio.gather(*[
            _fetch_listings({"areas": {"any": [aid]}, **date_filter}, pages_to_fetch, fetch_from_start)
            for aid in area_ids
        ])
        seen_ra_ids: set = set()
        for _, batch in zip(area_ids, area_batches):
            for r in batch:
                rid = r.get("ra_event_id") or r.get("external_id")
                if rid and rid in seen_ra_ids:
                    continue
                seen_ra_ids.add(rid)
                results.append(r)

    # ── keyword filter ───────────────────────────────────────────────────────
    if words:
        results = [r for r in results if _keyword_matches(r, words)]

    results.sort(key=lambda r: r.get("event_date") or date.min, reverse=True)

    filtered_total = len(results)
    start = (page - 1) * page_size
    results = results[start: start + page_size]

    return {
        "results": results,
        "total": filtered_total,
        "page": page,
        "page_size": page_size,
    }

async def fetch_event(event_id: str) -> Optional[dict]:
    """Fetch a single RA event by its numeric event ID."""
    payload = {
        "query": _SINGLE_EVENT_QUERY,
        "variables": {"id": event_id},
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(RA_GRAPHQL_URL, json=payload, headers=_HEADERS)
        response.raise_for_status()
        data = response.json()

    event = data.get("data", {}).get("event")
    if not event:
        return None
    return parse_ra_event(event)


def parse_ra_event(raw: dict) -> dict:
    """Convert a raw RA Event dict to an EventCreate-compatible dict."""
    venue_data = raw.get("venue") or {}
    area_data = venue_data.get("area") or {}
    country_data = area_data.get("country") or {}

    venue_name = venue_data.get("name", "")
    area_name = area_data.get("name", "")
    country_name = country_data.get("name", "")

    venue_parts = [p for p in [venue_name, area_name, country_name] if p]
    venue_location = ", ".join(venue_parts) if venue_parts else None

    artists = raw.get("artists") or []
    artist_names = ", ".join(a["name"].strip() for a in artists if a.get("name"))
    # Fall back to lineup string if no structured artists
    if not artist_names:
        artist_names = (raw.get("lineup") or "").replace("\n", ", ").strip(", ")

    images = raw.get("images") or []
    thumbnail_url = None
    if images and images[0].get("filename"):
        thumbnail_url = images[0]["filename"]
    if not thumbnail_url:
        thumbnail_url = raw.get("flyerFront")

    start_time = raw.get("startTime")
    event_date = None
    if start_time:
        try:
            from datetime import datetime
            event_date = datetime.fromisoformat(start_time.replace("Z", "+00:00")).date()
        except Exception:
            pass

    content_url = raw.get("contentUrl", "")
    ticket_url = f"https://ra.co{content_url}" if content_url else None

    event_title = raw.get("title") or "Unknown Event"
    title_parts = [p for p in [artist_names or event_title, f"at {venue_name}" if venue_name else None] if p]
    title = " ".join(title_parts)

    # Use listing id for external_id dedup; keep the event's own id for fetching
    listing_id = raw.get("_listing_id")
    event_node_id = raw.get("id")
    external_id_suffix = listing_id or event_node_id

    # Truncate fields that map to VARCHAR(255) columns.
    # Festival lineups can have hundreds of artists — store a preview in dj_name
    # and keep the full list available via the event_name / description fields.
    def _trunc(s: Optional[str], n: int) -> Optional[str]:
        if s and len(s) > n:
            return s[:n - 1] + "…"
        return s

    return {
        "title": _trunc(title, 255),
        "dj_name": _trunc(artist_names or "Unknown", 255),
        "event_name": event_title,
        "event_date": event_date,
        "venue_location": venue_location,
        "thumbnail_url": thumbnail_url,
        "description": None,
        "ticket_url": ticket_url,
        "external_id": f"ra_{external_id_suffix}",
        # The event's own node ID, needed for single-event GraphQL fetch
        "ra_event_id": str(event_node_id) if event_node_id else str(external_id_suffix),
    }
