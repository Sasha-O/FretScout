"""Pydantic models for FretScout."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class Listing(BaseModel):
    """Represents a used/vintage guitar listing."""

    listing_id: str
    title: str
    price: Optional[float] = None
    shipping: Optional[float] = None
    all_in_price: Optional[float] = None
    condition: Optional[str] = None
    location: Optional[str] = None
    url: HttpUrl
    source: str
    deal_label: Optional[Literal["Good", "Fair", "High"]] = None
    deal_confidence: Optional[Literal["High", "Medium", "Low"]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SavedAlert(BaseModel):
    """Represents a saved search alert."""

    alert_id: Optional[int] = None
    query: str
    max_price: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AlertEvent(BaseModel):
    """Represents an alert event generated from a listing match."""

    event_id: Optional[int] = None
    alert_id: int
    listing_id: Optional[str] = None
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
