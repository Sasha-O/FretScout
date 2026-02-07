"""Alert management utilities for FretScout."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

import sqlite3

from fretscout.models import AlertEvent, Listing, SavedAlert


def save_alert(
    connection: sqlite3.Connection, query: str, max_price: Optional[float]
) -> SavedAlert:
    """Persist a saved alert and return the saved model."""

    created_at = datetime.utcnow().isoformat()
    cursor = connection.execute(
        "INSERT INTO saved_alerts (query, max_price, created_at) VALUES (?, ?, ?)",
        (query, max_price, created_at),
    )
    connection.commit()
    return SavedAlert(
        alert_id=cursor.lastrowid, query=query, max_price=max_price, created_at=created_at
    )


def list_saved_alerts(connection: sqlite3.Connection) -> List[SavedAlert]:
    """Return all saved alerts."""

    rows = connection.execute(
        "SELECT alert_id, query, max_price, created_at FROM saved_alerts ORDER BY created_at DESC"
    ).fetchall()
    return [
        SavedAlert(
            alert_id=row["alert_id"],
            query=row["query"],
            max_price=row["max_price"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


def create_alert_event(
    connection: sqlite3.Connection,
    alert_id: int,
    listing_id: Optional[str],
    message: str,
) -> AlertEvent:
    """Create and return an alert event."""

    created_at = datetime.utcnow().isoformat()
    cursor = connection.execute(
        "INSERT INTO alert_events (alert_id, listing_id, message, created_at) VALUES (?, ?, ?, ?)",
        (alert_id, listing_id, message, created_at),
    )
    connection.commit()
    return AlertEvent(
        event_id=cursor.lastrowid,
        alert_id=alert_id,
        listing_id=listing_id,
        message=message,
        created_at=created_at,
    )


def list_alert_events(connection: sqlite3.Connection) -> List[AlertEvent]:
    """Return all alert events."""

    rows = connection.execute(
        "SELECT event_id, alert_id, listing_id, message, created_at "
        "FROM alert_events ORDER BY created_at DESC"
    ).fetchall()
    return [
        AlertEvent(
            event_id=row["event_id"],
            alert_id=row["alert_id"],
            listing_id=row["listing_id"],
            message=row["message"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


def generate_alert_events(
    connection: sqlite3.Connection,
    alerts: Iterable[SavedAlert],
    listings: Iterable[Listing],
) -> List[AlertEvent]:
    """Create alert events for listings that match saved alerts."""

    events: List[AlertEvent] = []
    for alert in alerts:
        normalized_query = alert.query.lower()
        for listing in listings:
            if normalized_query not in listing.title.lower():
                continue
            if alert.max_price is not None and listing.all_in_price > alert.max_price:
                continue
            message = (
                f"Match found: {listing.title} at ${listing.all_in_price:,.2f}"
            )
            events.append(
                create_alert_event(
                    connection,
                    alert_id=alert.alert_id or 0,
                    listing_id=listing.listing_id,
                    message=message,
                )
            )
    return events

