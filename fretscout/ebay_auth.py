"""eBay OAuth helpers for application access tokens."""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Optional

from fretscout.config import get_secret

EBAY_SCOPE_DEFAULT = "https://api.ebay.com/oauth/api_scope"
EBAY_ENV_PRODUCTION = "production"
EBAY_ENV_SANDBOX = "sandbox"
EBAY_TOKEN_ENDPOINTS: dict[str, str] = {
    EBAY_ENV_PRODUCTION: "https://api.ebay.com/identity/v1/oauth2/token",
    EBAY_ENV_SANDBOX: "https://api.sandbox.ebay.com/identity/v1/oauth2/token",
}

_EXPIRY_BUFFER_SECONDS = 120
_DISK_CACHE_PATH = Path.home() / ".fretscout" / "ebay_token.json"


@dataclass
class _TokenCacheEntry:
    token: str
    expires_at: float
    token_type: str
    scopes: tuple[str, ...]
    env: str


_token_cache: dict[tuple[str, tuple[str, ...]], _TokenCacheEntry] = {}


def get_ebay_env() -> Literal["production", "sandbox"]:
    """Return the configured eBay environment."""

    raw_env = (get_secret("EBAY_ENV") or EBAY_ENV_PRODUCTION).strip().lower()
    if raw_env in {EBAY_ENV_PRODUCTION, EBAY_ENV_SANDBOX}:
        return raw_env  # type: ignore[return-value]
    raise ValueError(
        "EBAY_ENV must be 'production' or 'sandbox' when provided."
    )


def clear_token_cache() -> None:
    """Clear the in-memory token cache."""

    _token_cache.clear()


def get_ebay_access_token(scopes: Optional[Iterable[str]] = None) -> str:
    """Return a cached or newly minted eBay OAuth access token."""

    scopes_tuple = _normalize_scopes(scopes)
    env = get_ebay_env()
    cache_key = (env, scopes_tuple)
    now = time.time()

    cached = _token_cache.get(cache_key)
    if cached and cached.expires_at - now > _EXPIRY_BUFFER_SECONDS:
        return cached.token

    cached = _load_disk_cache(cache_key, now)
    if cached:
        _token_cache[cache_key] = cached
        return cached.token

    token_entry = _request_new_token(env, scopes_tuple)
    _token_cache[cache_key] = token_entry
    _save_disk_cache(token_entry)
    return token_entry.token


def _normalize_scopes(scopes: Optional[Iterable[str]]) -> tuple[str, ...]:
    if not scopes:
        return (EBAY_SCOPE_DEFAULT,)
    normalized = tuple(scope.strip() for scope in scopes if scope.strip())
    return normalized or (EBAY_SCOPE_DEFAULT,)


def _request_new_token(env: str, scopes: tuple[str, ...]) -> _TokenCacheEntry:
    client_id = get_secret("EBAY_CLIENT_ID")
    client_secret = get_secret("EBAY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError(
            "Missing eBay credentials. Set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET."
        )

    token_url = EBAY_TOKEN_ENDPOINTS[env]
    auth_header = _build_basic_auth(client_id, client_secret)
    body = urllib.parse.urlencode(
        {"grant_type": "client_credentials", "scope": " ".join(scopes)}
    ).encode("utf-8")
    request = urllib.request.Request(
        token_url,
        data=body,
        method="POST",
        headers={
            "Authorization": auth_header,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        snippet = ""
        try:
            snippet = exc.read().decode("utf-8")[:200]
        except Exception:
            snippet = "<no response body>"
        raise RuntimeError(
            f"eBay OAuth request failed ({exc.code}): {snippet}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"eBay OAuth request failed to connect: {exc.reason}"
        ) from exc

    token = payload.get("access_token")
    expires_in = payload.get("expires_in")
    token_type = payload.get("token_type", "")
    if not token or not isinstance(expires_in, int):
        raise RuntimeError("eBay OAuth response missing access_token or expires_in.")

    expires_at = time.time() + int(expires_in)
    return _TokenCacheEntry(
        token=token,
        expires_at=expires_at,
        token_type=str(token_type),
        scopes=scopes,
        env=env,
    )


def _build_basic_auth(client_id: str, client_secret: str) -> str:
    credentials = f"{client_id}:{client_secret}".encode("utf-8")
    encoded = base64.b64encode(credentials).decode("ascii")
    return f"Basic {encoded}"


def _load_disk_cache(
    cache_key: tuple[str, tuple[str, ...]], now: float
) -> Optional[_TokenCacheEntry]:
    try:
        if not _DISK_CACHE_PATH.exists():
            return None
        payload = json.loads(_DISK_CACHE_PATH.read_text())
        if payload.get("env") != cache_key[0]:
            return None
        if tuple(payload.get("scopes", [])) != cache_key[1]:
            return None
        expires_at = float(payload.get("expires_at", 0))
        if expires_at - now <= _EXPIRY_BUFFER_SECONDS:
            return None
        token = payload.get("token")
        token_type = payload.get("token_type", "")
        if not token:
            return None
        return _TokenCacheEntry(
            token=token,
            expires_at=expires_at,
            token_type=str(token_type),
            scopes=cache_key[1],
            env=cache_key[0],
        )
    except Exception:
        return None


def _save_disk_cache(token_entry: _TokenCacheEntry) -> None:
    try:
        _DISK_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "token": token_entry.token,
            "expires_at": token_entry.expires_at,
            "token_type": token_entry.token_type,
            "scopes": list(token_entry.scopes),
            "env": token_entry.env,
        }
        _DISK_CACHE_PATH.write_text(json.dumps(payload))
    except Exception:
        return None
