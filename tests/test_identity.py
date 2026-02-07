"""Tests for listing identity utilities."""

from __future__ import annotations

from fretscout.listing_identity import ensure_listing_id
from fretscout.models import Listing


def _construct_listing(**kwargs) -> Listing:
    if hasattr(Listing, "model_construct"):
        return Listing.model_construct(**kwargs)
    return Listing.construct(**kwargs)


def test_preserves_existing_listing_id() -> None:
    listing = Listing(
        listing_id="custom-id",
        title="Test",
        url="https://example.com/listing",
        source="stub",
    )

    result = ensure_listing_id(listing)

    assert result is listing
    assert result.listing_id == "custom-id"


def test_source_item_id_generates_listing_id() -> None:
    listing = Listing(
        listing_id="",
        source="ebay",
        source_item_id="123",
        title="Test",
        url="https://example.com/listing",
    )

    result = ensure_listing_id(listing)

    assert result.listing_id == "ebay:123"


def test_url_hash_is_deterministic() -> None:
    listing_a = Listing(
        listing_id="",
        source="stub",
        title="Test",
        url="HTTPS://Example.com/Listings/123?b=2&a=1",
    )
    listing_b = Listing(
        listing_id="",
        source="stub",
        title="Test",
        url="https://example.com/listings/123?a=1&b=2",
    )

    result_a = ensure_listing_id(listing_a)
    result_b = ensure_listing_id(listing_b)

    assert result_a.listing_id == result_b.listing_id
    assert result_a.listing_id.startswith("url:")


def test_fallback_hash_is_deterministic() -> None:
    listing_a = _construct_listing(
        listing_id="",
        source="stub",
        title="Fallback",
        url=None,
    )
    listing_b = _construct_listing(
        listing_id="",
        source="stub",
        title="Fallback",
        url=None,
    )

    result_a = ensure_listing_id(listing_a)
    result_b = ensure_listing_id(listing_b)

    assert result_a.listing_id == result_b.listing_id
    assert result_a.listing_id.startswith("hash:")
