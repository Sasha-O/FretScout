"""Run a basic smoke test for the FretScout stack."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import fretscout.alerts
import fretscout.connectors.stub
import fretscout.db
import fretscout.models
import fretscout.valuation


def main() -> int:
    """Execute a smoke test run."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "fretscout_smoke.db"
        connection = fretscout.db.initialize_database(db_path)

        listings = fretscout.connectors.stub.fetch_listings("Fender")
        if not listings:
            print("Smoke test failed: no listings returned from stub connector.")
            return 1

        scored_listings = fretscout.valuation.score_listings(listings)
        for listing in scored_listings:
            estimated_value = fretscout.valuation.estimate_value(listing)
            deal_score = fretscout.valuation.deal_score(listing)
            if not isinstance(estimated_value, str) or not isinstance(deal_score, str):
                print("Smoke test failed: valuation outputs are not strings.")
                return 1
            if listing.deal_confidence not in {"High", "Medium", "Low"}:
                print("Smoke test failed: deal confidence not assigned.")
                return 1

        saved_alert = fretscout.alerts.save_alert(
            connection, query="Fender", max_price=5000.0
        )
        events = fretscout.alerts.generate_alert_events(
            connection, alerts=[saved_alert], listings=listings
        )
        if not events:
            print("Smoke test failed: no alert events generated.")
            return 1

    print("SMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
