"""eBay Browse API source utilities."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable, Optional

from fretscout import ebay_auth
from fretscout.config import get_secret
from fretscout.models import Listing

_DEFAULT_LIMIT = 50
_MAX_LIMIT = 200
_DEFAULT_MARKETPLACE = "EBAY_US"
_BACKOFF_SECONDS = (0.5, 1.0, 2.0)

_BASE_URLS = {
    "production": "https://api.ebay.com/buy/browse/v1/item_summary/search",
    "sandbox": "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search",
}


@dataclass
class EbaySearchParams:
    """Configuration for eBay Browse API search requests."""

    q: str
    limit: int = _DEFAULT_LIMIT
    offset: int = 0
    marketplace_id: str = _DEFAULT_MARKETPLACE
    category_ids: Optional[list[int]] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    condition_ids: Optional[list[str]] = None
    buying_options: Optional[list[str]] = None

    def clamp(self) -> "EbaySearchParams":
        """Return a copy with normalized limits."""

        limit = max(1, min(self.limit, _MAX_LIMIT))
        offset = max(0, self.offset)
        return EbaySearchParams(
            q=self.q,
            limit=limit,
            offset=offset,
            marketplace_id=self.marketplace_id,
            category_ids=self.category_ids,
            min_price=self.min_price,
            max_price=self.max_price,
            condition_ids=self.condition_ids,
            buying_options=self.buying_options,
        )


def search_ebay_listings(
    q: str,
    *,
    limit: int = _DEFAULT_LIMIT,
    offset: int = 0,
    category_ids: Optional[list[int]] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    marketplace_id: Optional[str] = None,
    env: Optional[str] = None,
) -> list[Listing]:
    """Search eBay listings and normalize results into Listing models."""

    params = EbaySearchParams(
        q=q,
        limit=limit,
        offset=offset,
        category_ids=category_ids,
        min_price=min_price,
        max_price=max_price,
        marketplace_id=marketplace_id or _default_marketplace(),
    ).clamp()
    env_effective = env or ebay_auth.get_ebay_env()
    base_url = _BASE_URLS.get(env_effective)
    if not base_url:
        raise ValueError("env must be 'production' or 'sandbox'.")

    request_url = _build_request_url(base_url, params)
    headers = _build_headers(params.marketplace_id, env=env_effective)
    request = urllib.request.Request(request_url, headers=headers, method="GET")

    data = _execute_request_with_retry(request)
    payload = json.loads(data.decode("utf-8"))
    return _normalize_listings(payload.get("itemSummaries", []) or [])


def _build_request_url(base_url: str, params: EbaySearchParams) -> str:
    query: dict[str, str] = {
        "q": params.q,
        "limit": str(params.limit),
        "offset": str(params.offset),
    }
    if params.category_ids:
        query["category_ids"] = ",".join(str(value) for value in params.category_ids)

    filters: list[str] = []
    if params.min_price is not None or params.max_price is not None:
        min_value = "" if params.min_price is None else _format_price(params.min_price)
        max_value = "" if params.max_price is None else _format_price(params.max_price)
        filters.append(f"price:[{min_value}..{max_value}]")

    if filters:
        query["filter"] = ",".join(filters)

    encoded = urllib.parse.urlencode(query, quote_via=urllib.parse.quote)
    return f"{base_url}?{encoded}"


def _format_price(value: float) -> str:
    return f"{float(value):.2f}"


def _build_headers(marketplace_id: str, *, env: str) -> dict[str, str]:
    token = ebay_auth.get_ebay_access_token(env=env)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
    }
    accept_language = _get_env_value("EBAY_ACCEPT_LANGUAGE")
    if accept_language:
        headers["Accept-Language"] = accept_language
    return headers


def _get_env_value(name: str) -> Optional[str]:
    return get_secret(name)


def _default_marketplace() -> str:
    return _get_env_value("EBAY_MARKETPLACE_ID") or _DEFAULT_MARKETPLACE


def _execute_request_with_retry(request: urllib.request.Request) -> bytes:
    last_error: Optional[Exception] = None
    for attempt, backoff in enumerate((0.0,) + _BACKOFF_SECONDS):
        if attempt:
            time.sleep(backoff)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code in {429, 500, 502, 503, 504}:
                last_error = exc
                continue
            snippet = _read_error_snippet(exc)
            raise RuntimeError(
                f"eBay search request failed ({exc.code}): {snippet}"
            ) from exc
        except urllib.error.URLError as exc:
            last_error = exc
            break

    if isinstance(last_error, urllib.error.HTTPError):
        snippet = _read_error_snippet(last_error)
        raise RuntimeError(
            f"eBay search request failed ({last_error.code}): {snippet}"
        ) from last_error
    if isinstance(last_error, urllib.error.URLError):
        raise RuntimeError(
            f"eBay search request failed to connect: {last_error.reason}"
        ) from last_error
    raise RuntimeError("eBay search request failed after retries.")


def _read_error_snippet(error: urllib.error.HTTPError) -> str:
    try:
        return error.read().decode("utf-8")[:200]
    except Exception:
        return "<no response body>"


def _normalize_listings(items: Iterable[dict]) -> list[Listing]:
    listings: list[Listing] = []
    for item in items:
        item_id = item.get("itemId")
        if not item_id:
            continue
        price = item.get("price") or {}
        shipping_options = item.get("shippingOptions") or []
        shipping_value = None
        if shipping_options:
            shipping_value = _parse_shipping(shipping_options[0])

        location_value = _format_location(item.get("itemLocation") or {})

        listings.append(
            Listing(
                listing_id=f"ebay:{item_id}",
                source="ebay",
                source_item_id=item_id,
                title=item.get("title") or "Untitled",
                price=_parse_float(price.get("value")),
                currency=price.get("currency"),
                shipping=shipping_value,
                condition=item.get("condition"),
                condition_id=item.get("conditionId"),
                url=item.get("itemWebUrl"),
                image_url=_image_url(item.get("image") or {}),
                seller=_seller_username(item.get("seller") or {}),
                location=location_value,
                all_in_price=_compute_all_in(price.get("value"), shipping_value),
                item_creation_date=item.get("itemCreationDate"),
                item_end_date=item.get("itemEndDate"),
            )
        )
    return listings


def _parse_float(value: object) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float, str)):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _parse_shipping(option: dict) -> Optional[float]:
    shipping_cost = option.get("shippingCost") or {}
    return _parse_float(shipping_cost.get("value"))


def _format_location(location: dict) -> Optional[str]:
    country = location.get("country")
    postal = location.get("postalCode")
    if country and postal:
        return f"{country} {postal}"
    return country or postal


def _image_url(image: dict) -> Optional[str]:
    return image.get("imageUrl")


def _seller_username(seller: dict) -> Optional[str]:
    return seller.get("username")


def _compute_all_in(price_value: object, shipping_value: Optional[float]) -> Optional[float]:
    price = _parse_float(price_value)
    if price is None:
        return None
    if shipping_value is None:
        return price
    return price + shipping_value
