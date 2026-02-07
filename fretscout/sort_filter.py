"""Sorting and filtering helpers for listings."""

from __future__ import annotations

from collections.abc import Iterable

from fretscout.models import Listing


def _normalize_confidence(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().lower() or None


def filter_listings(
    listings: Iterable[Listing],
    min_score: float,
    high_conf_only: bool,
) -> list[Listing]:
    """Filter listings by minimum deal score and confidence."""

    filtered = list(listings)
    if min_score > 0:
        filtered = [
            listing
            for listing in filtered
            if listing.deal_score is not None and listing.deal_score >= min_score
        ]
    if high_conf_only:
        filtered = [
            listing
            for listing in filtered
            if _normalize_confidence(listing.deal_confidence) == "high"
        ]
    return filtered


def sort_listings(listings: Iterable[Listing], sort_mode: str) -> list[Listing]:
    """Sort listings using the selected sort mode."""

    listings_list = list(listings)
    if sort_mode == "Relevance":
        return listings_list

    indexed = list(enumerate(listings_list))

    if sort_mode == "Price (low→high)":
        return [
            listing
            for _, listing in sorted(
                indexed,
                key=lambda pair: (
                    pair[1].price is None,
                    pair[1].price if pair[1].price is not None else float("inf"),
                    pair[0],
                ),
            )
        ]

    if sort_mode == "Deal Score (best→worst)":
        confidence_rank = {"high": 0, "medium": 1, "low": 2, None: 3}

        def sort_key(pair: tuple[int, Listing]) -> tuple:
            index, listing = pair
            confidence = _normalize_confidence(listing.deal_confidence)
            rank = confidence_rank.get(confidence, 3)
            score = listing.deal_score
            score_missing = score is None
            score_key = -score if score is not None else 0
            price_missing = listing.price is None
            price_key = listing.price if listing.price is not None else float("inf")
            return (
                rank,
                score_missing,
                score_key,
                price_missing,
                price_key,
                index,
            )

        return [listing for _, listing in sorted(indexed, key=sort_key)]

    return listings_list
