"""Stub connector returning sample used guitar listings."""

from __future__ import annotations

from typing import List

from fretscout.models import Listing


SAMPLE_LISTINGS = [
    {
        "listing_id": "reverb-001",
        "title": "Fender American Vintage '62 Stratocaster",
        "price": 1899.0,
        "shipping": 85.0,
        "condition": "Very Good",
        "location": "Austin, TX",
        "url": "https://example.com/listings/reverb-001",
        "source": "Reverb (Stub)",
    },
    {
        "listing_id": "ebay-002",
        "title": "Gibson Les Paul Standard 1998",
        "price": 2295.0,
        "shipping": 120.0,
        "condition": "Good",
        "location": "Nashville, TN",
        "url": "https://example.com/listings/ebay-002",
        "source": "eBay (Stub)",
    },
    {
        "listing_id": "gc-003",
        "title": "Martin D-28 Vintage 1974",
        "price": 3199.0,
        "shipping": 140.0,
        "condition": "Excellent",
        "location": "Chicago, IL",
        "url": "https://example.com/listings/gc-003",
        "source": "Guitar Center (Stub)",
    },
    {
        "listing_id": "cl-004",
        "title": "PRS Custom 24 10-Top",
        "price": 2599.0,
        "shipping": 95.0,
        "condition": "Very Good",
        "location": "Portland, OR",
        "url": "https://example.com/listings/cl-004",
        "source": "Craigslist (Stub)",
    },
]


def fetch_listings(query: str) -> List[Listing]:
    """Return hardcoded listings filtered by a query substring."""

    normalized_query = query.strip().lower()
    listings: List[Listing] = []
    for entry in SAMPLE_LISTINGS:
        if normalized_query and normalized_query not in entry["title"].lower():
            continue
        all_in_price = entry["price"] + entry["shipping"]
        listings.append(
            Listing(
                **entry,
                all_in_price=all_in_price,
            )
        )
    return listings

