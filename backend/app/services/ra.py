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


async def area_id_for_name(city: str) -> Optional[int]:
    """Resolve a city name to an RA area integer ID."""
    payload = {
        "query": _AREA_SEARCH_QUERY,
        "variables": {"searchTerm": city, "limit": 5},
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(RA_GRAPHQL_URL, json=payload, headers=_HEADERS)
        response.raise_for_status()
        data = response.json()

    areas = data.get("data", {}).get("areas") or []
    if not areas:
        return None
    # Return the first match's ID as int
    return int(areas[0]["id"])


async def search_events(
    location: str,
    keyword: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Search RA events by location (city name) and optional keyword/date range.

    RA's GraphQL title filter only supports exact match, so when a keyword is
    provided we fetch a larger batch and filter client-side.
    """
    area_id = await area_id_for_name(location)
    if area_id is None:
        return {"results": [], "total": 0, "page": page, "page_size": page_size}

    filters: dict = {"areas": {"any": [area_id]}}

    # Always apply a date window. Default to last 5 years → today if not specified,
    # so results are relevant rather than showing events from the early 2000s.
    from datetime import datetime, timedelta
    today = date.today()
    effective_from = date_from or (today - timedelta(days=730))  # default: last 2 years
    effective_to = date_to or today

    filters["listingDate"] = {
        "gte": f"{effective_from.isoformat()}T00:00:00",
        "lte": f"{effective_to.isoformat()}T23:59:59",
    }

    fetch_size = 100  # RA's max page size
    # Busy cities (e.g. Melbourne) have 300+ events/month, so the last page
    # only covers a few days. When keyword-searching, pull the last 5 pages
    # (~500 events ≈ last 6-8 weeks) to cover a reasonable lookback window.
    pages_to_fetch = 5 if keyword else 1

    import asyncio

    async with httpx.AsyncClient(timeout=20.0) as client:
        # Step 1: get total count so we can jump to the last N pages
        count_payload = {
            "query": _EVENTS_QUERY,
            "variables": {"filters": filters, "pageSize": 1, "page": 1},
        }
        count_resp = await client.post(RA_GRAPHQL_URL, json=count_payload, headers=_HEADERS)
        count_resp.raise_for_status()
        total_results = (
            count_resp.json()
            .get("data", {})
            .get("eventListings", {})
            .get("totalResults", 0)
        ) or 0

        last_page = max(1, -(-total_results // fetch_size))  # ceiling division
        target_pages = list(range(max(1, last_page - pages_to_fetch + 1), last_page + 1))

        # Step 2: fetch target pages concurrently
        async def fetch_page(p):
            resp = await client.post(RA_GRAPHQL_URL, json={
                "query": _EVENTS_QUERY,
                "variables": {"filters": filters, "pageSize": fetch_size, "page": p},
            }, headers=_HEADERS)
            resp.raise_for_status()
            return resp.json()

        pages_data = await asyncio.gather(*[fetch_page(p) for p in target_pages])

    raw_listings = []
    for data in pages_data:
        raw_listings += data.get("data", {}).get("eventListings", {}).get("data", [])

    results = []
    for listing in raw_listings:
        event = listing.get("event")
        if event:
            event["_listing_id"] = listing.get("id")
            results.append(parse_ra_event(event))

    # Sort most-recent first
    results.sort(key=lambda r: r.get("event_date") or date.min, reverse=True)

    # Client-side keyword filter
    if keyword:
        kw = keyword.lower()
        results = [
            r for r in results
            if kw in (r.get("title") or "").lower()
            or kw in (r.get("dj_name") or "").lower()
            or kw in (r.get("event_name") or "").lower()
            or kw in (r.get("venue_location") or "").lower()
        ]

    filtered_total = len(results)
    start = (page - 1) * page_size
    results = results[start: start + page_size]

    return {
        "results": results,
        "total": filtered_total,
        "page": page,
        "page_size": page_size,
    }


async def fetch_event(ra_id: str) -> Optional[dict]:
    """Fetch a single RA event by its event ID."""
    payload = {
        "query": _SINGLE_EVENT_QUERY,
        "variables": {"id": ra_id},
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

    # Use event id for external_id (listing id if available)
    event_id = raw.get("_listing_id") or raw.get("id")

    return {
        "title": title,
        "dj_name": artist_names or "Unknown",
        "event_name": event_title,
        "event_date": event_date,
        "venue_location": venue_location,
        "thumbnail_url": thumbnail_url,
        "description": None,
        "ticket_url": ticket_url,
        "external_id": f"ra_{event_id}",
    }
