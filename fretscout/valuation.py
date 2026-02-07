"""Valuation helpers for FretScout."""

from __future__ import annotations

from statistics import median
from typing import Iterable

from fretscout.models import Listing


def estimate_value(listing: Listing) -> str:
    """Return an estimated market value for a listing."""

    _ = listing
    return "N/A"


def deal_score(listing: Listing) -> str:
    """Return a deal score or assessment for a listing."""

    _ = listing
    return "N/A"


def _parse_price(value: object) -> float | None:
    """Return a float price if valid."""

    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _all_in_price(listing: Listing) -> float | None:
    """Return the all-in price for a listing."""

    price = _parse_price(listing.price)
    if price is None:
        return None
    shipping = _parse_price(listing.shipping) or 0.0
    return price + shipping


def _confidence_level(listing: Listing) -> str:
    """Return a deterministic confidence level for a listing."""

    has_title = bool(listing.title and listing.title.strip())
    has_condition = bool(listing.condition and listing.condition.strip())
    has_price = _parse_price(listing.price) is not None

    if has_title and has_condition and has_price:
        return "High"
    if has_title and has_price:
        return "Medium"
    return "Low"


def score_listings(listings: Iterable[Listing]) -> list[Listing]:
    """Annotate listings with deal labels and confidence levels."""

    listings_list = list(listings)
    priced = [price for listing in listings_list if (price := _all_in_price(listing)) is not None]

    if len(priced) >= 3:
        benchmark = median(priced)
    else:
        benchmark = None

    scored: list[Listing] = []
    for listing in listings_list:
        all_in = _all_in_price(listing)
        if benchmark is None or all_in is None:
            label = None
        elif all_in <= benchmark * 0.90:
            label = "Good"
        elif all_in < benchmark * 1.10:
            label = "Fair"
        else:
            label = "High"

        confidence = _confidence_level(listing)
        scored.append(
            listing.model_copy(
                update={
                    "deal_label": label,
                    "deal_confidence": confidence,
                }
            )
        )

    return scored
