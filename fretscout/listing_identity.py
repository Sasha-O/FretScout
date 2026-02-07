"""Utilities for deterministic listing identity."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fretscout.models import Listing

_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_text(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value.strip().lower())


def _normalize_url(value: str) -> str:
    cleaned = value.strip()
    parts = urlsplit(cleaned)
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = re.sub(r"/{2,}", "/", parts.path or "")
    if path.endswith("/") and path != "/":
        path = path.rstrip("/")

    query_pairs = parse_qsl(parts.query, keep_blank_values=True)
    filtered_pairs: list[tuple[str, str]] = []
    for key, val in query_pairs:
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in {
            "gclid",
            "fbclid",
            "mc_cid",
            "mc_eid",
            "yclid",
        }:
            continue
        filtered_pairs.append((key, val))
    query = urlencode(filtered_pairs, doseq=True)
    # Drop fragment since it is rarely identity-bearing.
    return urlunsplit((scheme, netloc, path, query, ""))


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _fallback_fingerprint(listing: Listing) -> str:
    parts = [
        listing.title,
        listing.source,
        listing.source_item_id,
        listing.seller,
        listing.location,
        listing.condition,
        listing.currency,
        listing.url,
        listing.price,
    ]
    normalized: list[str] = []
    for part in parts:
        if part is None:
            normalized.append("")
        elif isinstance(part, str):
            if part.startswith("http"):
                normalized.append(_normalize_url(part))
            else:
                normalized.append(_normalize_text(part))
        else:
            normalized.append(str(part))
    return "|".join(normalized)


def ensure_listing_id(listing: Listing) -> Listing:
    """Ensure a listing has a deterministic listing_id."""

    if listing.listing_id and listing.listing_id.strip():
        return listing

    listing_id: str
    if listing.source and listing.source_item_id:
        listing_id = f"{listing.source}:{listing.source_item_id}"
    elif listing.url:
        listing_id = f"url:{_hash_text(_normalize_url(str(listing.url)))}"
    else:
        listing_id = f"hash:{_hash_text(_fallback_fingerprint(listing))}"

    return listing.model_copy(update={"listing_id": listing_id})


def ensure_listing_ids(listings: list[Listing]) -> list[Listing]:
    """Ensure listing IDs for a collection of listings."""

    return [ensure_listing_id(listing) for listing in listings]
