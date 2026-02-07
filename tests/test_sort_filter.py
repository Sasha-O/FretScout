"""Tests for listing sort and filter helpers."""

from __future__ import annotations

from fretscout.models import Listing
from fretscout.sort_filter import filter_listings, sort_listings


def build_listing(
    listing_id: str,
    price: float | None,
    deal_score: float | None,
    deal_confidence: str | None,
) -> Listing:
    """Create a listing for sorting/filtering tests."""

    return Listing(
        listing_id=listing_id,
        title=f"Listing {listing_id}",
        price=price,
        url=f"https://example.com/{listing_id}",
        source="test",
        deal_score=deal_score,
        deal_confidence=deal_confidence,
    )


def test_sort_relevance_preserves_order() -> None:
    """Relevance sort should preserve the incoming order."""

    listings = [
        build_listing("a", 100.0, 80.0, "high"),
        build_listing("b", 90.0, 70.0, "medium"),
        build_listing("c", 110.0, 60.0, "low"),
    ]

    sorted_listings = sort_listings(listings, "Relevance")

    assert [listing.listing_id for listing in sorted_listings] == ["a", "b", "c"]


def test_sort_price_missing_last() -> None:
    """Price sort should send missing prices to the end."""

    listings = [
        build_listing("a", None, 80.0, "high"),
        build_listing("b", 90.0, 70.0, "medium"),
        build_listing("c", 110.0, 60.0, "low"),
    ]

    sorted_listings = sort_listings(listings, "Price (low→high)")

    assert [listing.listing_id for listing in sorted_listings] == ["b", "c", "a"]


def test_sort_deal_score_by_confidence_then_score() -> None:
    """Deal score sort should respect confidence and score ordering."""

    listings = [
        build_listing("a", 120.0, 70.0, "medium"),
        build_listing("b", 100.0, 80.0, "high"),
        build_listing("c", 90.0, None, None),
        build_listing("d", 110.0, 60.0, "high"),
        build_listing("e", 95.0, 80.0, "low"),
    ]

    sorted_listings = sort_listings(listings, "Deal Score (best→worst)")

    assert [listing.listing_id for listing in sorted_listings] == [
        "b",
        "d",
        "a",
        "e",
        "c",
    ]


def test_filter_min_deal_score_excludes_unscored() -> None:
    """Minimum deal score should exclude None or below threshold."""

    listings = [
        build_listing("a", 100.0, 80.0, "high"),
        build_listing("b", 90.0, None, "medium"),
        build_listing("c", 110.0, 60.0, "low"),
    ]

    filtered = filter_listings(listings, min_score=70, high_conf_only=False)

    assert [listing.listing_id for listing in filtered] == ["a"]


def test_filter_high_confidence_only() -> None:
    """High confidence filter should keep only high confidence listings."""

    listings = [
        build_listing("a", 100.0, 80.0, "high"),
        build_listing("b", 90.0, 70.0, "medium"),
        build_listing("c", 110.0, 60.0, None),
    ]

    filtered = filter_listings(listings, min_score=0, high_conf_only=True)

    assert [listing.listing_id for listing in filtered] == ["a"]
