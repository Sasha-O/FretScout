"""Tests for the eBay source integration."""

from __future__ import annotations

from io import BytesIO
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

import fretscout.sources.ebay as ebay_source


class DummyResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self) -> "DummyResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def _fixture_payload() -> bytes:
    return (
        b"{"
        b"\"itemSummaries\":["
        b"{"
        b"\"itemId\":\"v1|123|0\","
        b"\"title\":\"Fender Strat\","
        b"\"price\":{\"value\":\"999.99\",\"currency\":\"USD\"},"
        b"\"image\":{\"imageUrl\":\"https://example.com/img.jpg\"},"
        b"\"itemWebUrl\":\"https://example.com/item\","
        b"\"shippingOptions\":[{\"shippingCost\":{\"value\":\"25.00\"}}],"
        b"\"seller\":{\"username\":\"seller1\"},"
        b"\"condition\":\"Used\","
        b"\"conditionId\":\"3000\","
        b"\"itemLocation\":{\"country\":\"US\",\"postalCode\":\"78701\"},"
        b"\"itemCreationDate\":\"2024-01-01\","
        b"\"itemEndDate\":\"2024-12-31\""
        b"}"
        b"]"
        b"}"
    )


def test_request_construction_production(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: urllib.request.Request, timeout: int = 30) -> DummyResponse:
        captured["url"] = request.full_url
        captured["headers"] = {key.lower(): value for key, value in request.headers.items()}
        return DummyResponse(_fixture_payload())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(ebay_source.ebay_auth, "get_ebay_access_token", lambda: "TEST_TOKEN")
    monkeypatch.setattr(ebay_source, "get_secret", lambda name: None)

    ebay_source.search_ebay_listings(
        "strat",
        limit=10,
        offset=5,
        category_ids=[3858],
        env="production",
    )

    parsed = urllib.parse.urlparse(captured["url"])
    query = urllib.parse.parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert "api.ebay.com" in parsed.netloc
    assert query["q"] == ["strat"]
    assert query["limit"] == ["10"]
    assert query["offset"] == ["5"]
    assert query["category_ids"] == ["3858"]
    assert captured["headers"]["authorization"] == "Bearer TEST_TOKEN"
    assert captured["headers"]["x-ebay-c-marketplace-id"] == "EBAY_US"


def test_request_construction_sandbox(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: urllib.request.Request, timeout: int = 30) -> DummyResponse:
        captured["url"] = request.full_url
        return DummyResponse(_fixture_payload())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(ebay_source.ebay_auth, "get_ebay_access_token", lambda: "TEST_TOKEN")
    monkeypatch.setattr(ebay_source, "get_secret", lambda name: None)

    ebay_source.search_ebay_listings("strat", env="sandbox")

    assert "api.sandbox.ebay.com" in captured["url"]


def test_response_parsing_and_mapping(monkeypatch) -> None:
    def fake_urlopen(request: urllib.request.Request, timeout: int = 30) -> DummyResponse:
        return DummyResponse(_fixture_payload())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(ebay_source.ebay_auth, "get_ebay_access_token", lambda: "TEST_TOKEN")
    monkeypatch.setattr(ebay_source, "get_secret", lambda name: None)

    listings = ebay_source.search_ebay_listings("strat", env="production")
    assert len(listings) == 1
    listing = listings[0]
    assert listing.listing_id == "ebay:v1|123|0"
    assert listing.source == "ebay"
    assert listing.source_item_id == "v1|123|0"
    assert listing.title == "Fender Strat"
    assert listing.price == 999.99
    assert listing.currency == "USD"
    assert str(listing.image_url) == "https://example.com/img.jpg"
    assert str(listing.url) == "https://example.com/item"
    assert listing.shipping == 25.0
    assert listing.condition == "Used"
    assert listing.condition_id == "3000"
    assert listing.seller == "seller1"
    assert listing.location == "US 78701"
    assert listing.item_creation_date == "2024-01-01"
    assert listing.item_end_date == "2024-12-31"


def test_retry_behavior(monkeypatch) -> None:
    payload = _fixture_payload()
    attempts = {"count": 0}

    def fake_urlopen(request: urllib.request.Request, timeout: int = 30) -> DummyResponse:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise urllib.error.HTTPError(
                request.full_url,
                429,
                "Too Many Requests",
                hdrs=None,
                fp=BytesIO(b"rate limit"),
            )
        return DummyResponse(payload)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(ebay_source.ebay_auth, "get_ebay_access_token", lambda: "TEST_TOKEN")
    monkeypatch.setattr(ebay_source, "get_secret", lambda name: None)

    listings = ebay_source.search_ebay_listings("strat")
    assert attempts["count"] == 2
    assert len(listings) == 1


def test_missing_optional_fields(monkeypatch) -> None:
    payload = (
        b"{"
        b"\"itemSummaries\":["
        b"{"
        b"\"itemId\":\"v1|999|0\","
        b"\"title\":\"No Image\","
        b"\"price\":{\"value\":\"1500\",\"currency\":\"USD\"},"
        b"\"itemWebUrl\":\"https://example.com/item2\""
        b"}"
        b"]"
        b"}"
    )

    def fake_urlopen(request: urllib.request.Request, timeout: int = 30) -> DummyResponse:
        return DummyResponse(payload)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(ebay_source.ebay_auth, "get_ebay_access_token", lambda: "TEST_TOKEN")
    monkeypatch.setattr(ebay_source, "get_secret", lambda name: None)

    listings = ebay_source.search_ebay_listings("strat")
    listing = listings[0]
    assert listing.image_url is None
    assert listing.shipping is None
