"""Tests for Pydantic models."""

from __future__ import annotations

import time

from fretscout.models import Listing


def test_listing_created_at_is_per_instance() -> None:
    """Ensure created_at defaults are per-instance timestamps."""

    first = Listing(
        listing_id="listing-1",
        title="Test Listing",
        price=1000.0,
        shipping=50.0,
        all_in_price=1050.0,
        url="https://example.com/listing-1",
        source="stub",
    )
    time.sleep(0.01)
    second = Listing(
        listing_id="listing-2",
        title="Test Listing 2",
        price=1100.0,
        shipping=60.0,
        all_in_price=1160.0,
        url="https://example.com/listing-2",
        source="stub",
    )

    assert second.created_at >= first.created_at
    assert second.created_at != first.created_at
