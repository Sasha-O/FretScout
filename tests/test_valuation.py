"""Tests for valuation scoring."""

from __future__ import annotations

from fretscout.models import Listing
from fretscout.valuation import score_listings


def build_listing(
    listing_id: str,
    title: str,
    price: float | None,
    shipping: float | None = None,
    condition: str | None = None,
) -> Listing:
    """Create a listing for valuation tests."""

    return Listing(
        listing_id=listing_id,
        title=title,
        price=price,
        shipping=shipping,
        condition=condition,
        url=f"https://example.com/{listing_id}",
        source="test",
    )


def test_score_listings_labels_with_median() -> None:
    """Score listings with a valid median benchmark."""

    listings = [
        build_listing("l1", "Good Listing", 100.0, 10.0),
        build_listing("l2", "Fair Listing", 150.0, 10.0),
        build_listing("l3", "High Listing", 200.0, 10.0),
    ]

    scored = score_listings(listings)
    labels = {listing.listing_id: listing.deal_label for listing in scored}

    assert labels["l1"] == "Good"
    assert labels["l2"] == "Fair"
    assert labels["l3"] == "High"


def test_missing_shipping_treated_as_zero() -> None:
    """Listings without shipping should still be scored."""

    listings = [
        build_listing("l1", "Listing 1", 100.0, None),
        build_listing("l2", "Listing 2", 100.0, 0.0),
        build_listing("l3", "Listing 3", 100.0, 0.0),
    ]

    scored = score_listings(listings)

    assert all(listing.deal_label == "Fair" for listing in scored)


def test_missing_price_listing_not_scored() -> None:
    """Listings without a price should not receive a deal label."""

    listings = [
        build_listing("l1", "Listing 1", 100.0, 10.0),
        build_listing("l2", "Listing 2", 150.0, 10.0),
        build_listing("l3", "Listing 3", 200.0, 10.0),
        build_listing("l4", "Listing 4", None, 10.0),
    ]

    scored = score_listings(listings)
    label_map = {listing.listing_id: listing.deal_label for listing in scored}

    assert label_map["l4"] is None
    assert label_map["l1"] is not None
    assert label_map["l2"] is not None
    assert label_map["l3"] is not None


def test_less_than_three_valid_priced_listings() -> None:
    """If fewer than three listings have prices, skip deal labels."""

    listings = [
        build_listing("l1", "Listing 1", 100.0, 10.0),
        build_listing("l2", "Listing 2", None, 10.0),
        build_listing("l3", "Listing 3", 200.0, 10.0),
    ]

    scored = score_listings(listings)

    assert all(listing.deal_label is None for listing in scored)


def test_confidence_levels() -> None:
    """Confidence is derived from listing completeness."""

    listings = [
        build_listing("l1", "Complete", 100.0, 10.0, condition="Excellent"),
        build_listing("l2", "Price Only", 150.0, 10.0),
        build_listing("l3", "", None, None),
    ]

    scored = score_listings(listings)
    confidence = {listing.listing_id: listing.deal_confidence for listing in scored}

    assert confidence["l1"] == "High"
    assert confidence["l2"] == "Medium"
    assert confidence["l3"] == "Low"
