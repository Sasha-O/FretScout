"""Manual smoke test for eBay OAuth."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import fretscout.ebay_auth


def main() -> int:
    """Acquire an eBay OAuth token and report status."""

    token = fretscout.ebay_auth.get_ebay_access_token()
    env = fretscout.ebay_auth.get_ebay_env()
    print(f"OK: token acquired, expires_in~{_expires_in_seconds()}s (env={env})")
    if not token:
        print("Failed to acquire token.")
        return 1
    return 0


def _expires_in_seconds() -> int:
    token_entry = fretscout.ebay_auth._token_cache.get(
        (fretscout.ebay_auth.get_ebay_env(), (fretscout.ebay_auth.EBAY_SCOPE_DEFAULT,))
    )
    if not token_entry:
        return 0
    return max(0, int(token_entry.expires_at - fretscout.ebay_auth.time.time()))


if __name__ == "__main__":
    sys.exit(main())
