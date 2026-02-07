"""Utilities for deduplicating listings deterministically."""

from __future__ import annotations

from fretscout.listing_identity import ensure_listing_ids
from fretscout.models import Listing


def _completeness_score(listing: Listing) -> int:
    fields = (
        "image_url",
        "url",
        "condition",
        "seller",
        "location",
        "currency",
        "price",
    )
    score = 0
    for field in fields:
        value = getattr(listing, field, None)
        if value not in (None, ""):
            score += 1
    return score


def dedupe_listings(listings: list[Listing]) -> list[Listing]:
    """Deduplicate listings by listing_id with deterministic selection."""

    normalized = ensure_listing_ids(listings)
    seen: dict[str, tuple[Listing, int]] = {}
    order: list[str] = []
    for listing in normalized:
        listing_id = listing.listing_id
        score = _completeness_score(listing)
        if listing_id not in seen:
            seen[listing_id] = (listing, score)
            order.append(listing_id)
            continue
        _, existing_score = seen[listing_id]
        if score > existing_score:
            seen[listing_id] = (listing, score)
    return [seen[listing_id][0] for listing_id in order]
