"""Tests for listing deduplication."""

from __future__ import annotations

from fretscout.dedup import dedupe_listings
from fretscout.models import Listing


def test_dedupe_removes_duplicate_ids() -> None:
    listing_a = Listing(
        listing_id="same",
        title="Listing A",
        url="https://example.com/a",
        source="stub",
    )
    listing_b = Listing(
        listing_id="same",
        title="Listing B",
        url="https://example.com/b",
        source="stub",
    )

    deduped = dedupe_listings([listing_a, listing_b])

    assert len(deduped) == 1
    assert deduped[0].listing_id == "same"


def test_dedupe_prefers_more_complete_record() -> None:
    listing_a = Listing(
        listing_id="same",
        title="Listing A",
        url="https://example.com/a",
        source="stub",
    )
    listing_b = Listing(
        listing_id="same",
        title="Listing B",
        url="https://example.com/b",
        source="stub",
        image_url="https://example.com/image.jpg",
        condition="Excellent",
        seller="TestSeller",
        location="Austin, TX",
        currency="USD",
        price=1000.0,
    )

    deduped = dedupe_listings([listing_a, listing_b])

    assert len(deduped) == 1
    assert deduped[0].image_url is not None
    assert deduped[0].title == "Listing B"


def test_dedupe_preserves_ordering() -> None:
    listing_a = Listing(
        listing_id="id-1",
        title="Listing A",
        url="https://example.com/a",
        source="stub",
    )
    listing_b = Listing(
        listing_id="id-2",
        title="Listing B",
        url="https://example.com/b",
        source="stub",
    )
    listing_c = Listing(
        listing_id="id-1",
        title="Listing C",
        url="https://example.com/c",
        source="stub",
        condition="Excellent",
    )

    deduped = dedupe_listings([listing_a, listing_b, listing_c])

    assert [listing.listing_id for listing in deduped] == ["id-1", "id-2"]
