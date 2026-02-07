"""Pydantic models for FretScout."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


class Listing(BaseModel):
    """Represents a used/vintage guitar listing."""

    listing_id: str
    title: str
    price: float
    shipping: float
    all_in_price: float
    condition: Optional[str] = None
    location: Optional[str] = None
    url: HttpUrl
    source: str
    created_at: datetime = datetime.utcnow()


class SavedAlert(BaseModel):
    """Represents a saved search alert."""

    alert_id: Optional[int] = None
    query: str
    max_price: Optional[float] = None
    created_at: datetime = datetime.utcnow()


class AlertEvent(BaseModel):
    """Represents an alert event generated from a listing match."""

    event_id: Optional[int] = None
    alert_id: int
    listing_id: Optional[str] = None
    message: str
    created_at: datetime = datetime.utcnow()

