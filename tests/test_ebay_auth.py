from __future__ import annotations

import base64
import json
import urllib.parse
from types import SimpleNamespace

import pytest

import fretscout.ebay_auth as ebay_auth


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_request_building_production(monkeypatch, tmp_path) -> None:
    captured = SimpleNamespace(request=None)

    def fake_urlopen(request, timeout=30):
        captured.request = request
        return FakeResponse({"access_token": "token", "expires_in": 3600, "token_type": "Bearer"})

    monkeypatch.setenv("EBAY_CLIENT_ID", "client-id")
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("EBAY_ENV", "production")
    monkeypatch.setattr(ebay_auth, "_DISK_CACHE_PATH", tmp_path / "ebay_token.json")
    monkeypatch.setattr(ebay_auth.urllib.request, "urlopen", fake_urlopen)
    ebay_auth.clear_token_cache()

    token = ebay_auth.get_ebay_access_token()

    assert token == "token"
    assert captured.request.full_url == ebay_auth.EBAY_TOKEN_ENDPOINTS["production"]
    auth_header = captured.request.headers.get("Authorization")
    expected_auth = base64.b64encode(b"client-id:client-secret").decode("ascii")
    assert auth_header == f"Basic {expected_auth}"
    body = captured.request.data.decode("utf-8")
    parsed = urllib.parse.parse_qs(body)
    assert parsed["grant_type"] == ["client_credentials"]
    assert parsed["scope"] == [ebay_auth.EBAY_SCOPE_DEFAULT]


def test_request_building_sandbox(monkeypatch, tmp_path) -> None:
    captured = SimpleNamespace(request=None)

    def fake_urlopen(request, timeout=30):
        captured.request = request
        return FakeResponse({"access_token": "token", "expires_in": 3600, "token_type": "Bearer"})

    monkeypatch.setenv("EBAY_CLIENT_ID", "client-id")
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("EBAY_ENV", "sandbox")
    monkeypatch.setattr(ebay_auth, "_DISK_CACHE_PATH", tmp_path / "ebay_token.json")
    monkeypatch.setattr(ebay_auth.urllib.request, "urlopen", fake_urlopen)
    ebay_auth.clear_token_cache()

    ebay_auth.get_ebay_access_token()

    assert captured.request.full_url == ebay_auth.EBAY_TOKEN_ENDPOINTS["sandbox"]


def test_caching_returns_cached_token(monkeypatch, tmp_path) -> None:
    calls = {"count": 0}

    def fake_urlopen(request, timeout=30):
        calls["count"] += 1
        return FakeResponse({"access_token": f"token-{calls['count']}", "expires_in": 3600, "token_type": "Bearer"})

    monkeypatch.setenv("EBAY_CLIENT_ID", "client-id")
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(ebay_auth, "_DISK_CACHE_PATH", tmp_path / "ebay_token.json")
    monkeypatch.setattr(ebay_auth.urllib.request, "urlopen", fake_urlopen)
    ebay_auth.clear_token_cache()

    first = ebay_auth.get_ebay_access_token()
    second = ebay_auth.get_ebay_access_token()

    assert first == second
    assert calls["count"] == 1


def test_near_expiry_refreshes(monkeypatch, tmp_path) -> None:
    calls = {"count": 0}

    def fake_urlopen(request, timeout=30):
        calls["count"] += 1
        return FakeResponse({"access_token": f"token-{calls['count']}", "expires_in": 100, "token_type": "Bearer"})

    monkeypatch.setenv("EBAY_CLIENT_ID", "client-id")
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(ebay_auth, "_DISK_CACHE_PATH", tmp_path / "ebay_token.json")
    monkeypatch.setattr(ebay_auth.urllib.request, "urlopen", fake_urlopen)
    ebay_auth.clear_token_cache()

    first = ebay_auth.get_ebay_access_token()
    second = ebay_auth.get_ebay_access_token()

    assert first != second
    assert calls["count"] == 2


def test_missing_credentials_raises(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("EBAY_CLIENT_ID", raising=False)
    monkeypatch.delenv("EBAY_CLIENT_SECRET", raising=False)
    monkeypatch.setattr(ebay_auth, "_DISK_CACHE_PATH", tmp_path / "ebay_token.json")
    ebay_auth.clear_token_cache()

    with pytest.raises(ValueError, match="Missing eBay credentials"):
        ebay_auth.get_ebay_access_token()
