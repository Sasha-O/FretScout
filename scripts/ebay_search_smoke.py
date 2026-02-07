"""Manual eBay search smoke script."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fretscout.sources.ebay import search_ebay_listings  # noqa: E402


def main() -> int:
    query = os.getenv("EBAY_SEARCH_QUERY", "fender stratocaster")
    limit = int(os.getenv("EBAY_SEARCH_LIMIT", "5"))

    try:
        listings = search_ebay_listings(query, limit=limit)
    except Exception as exc:
        print(f"eBay search smoke failed: {exc}")
        return 1

    print(f"OK: got {len(listings)} items")
    for listing in listings[:2]:
        price = listing.price if listing.price is not None else "N/A"
        currency = listing.currency or ""
        print(f"- {listing.title} ({price} {currency})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
