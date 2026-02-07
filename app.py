"""Streamlit application for FretScout MVP."""

from __future__ import annotations

from typing import Optional

import streamlit as st

from fretscout import alerts as alert_service
from fretscout.config import get_secret
from fretscout.connectors import stub as stub_connector
from fretscout.dedup import dedupe_listings
from fretscout.db import initialize_database
from fretscout.listing_identity import ensure_listing_ids
from fretscout.sources import ebay as ebay_source
from fretscout.sort_filter import filter_listings, sort_listings
from fretscout.valuation import score_listings


def format_price(value: Optional[float]) -> str:
    """Format a numeric value as a price string."""

    if value is None:
        return "N/A"
    return f"${value:,.2f}"


def format_percent(value: Optional[float]) -> str:
    """Format a numeric value as a signed percent string."""

    if value is None:
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%"


def render_listing(listing) -> None:
    """Render a listing card."""

    st.subheader(listing.title)
    st.caption(f"Source: {listing.source}")
    st.write(
        f"**All-in price:** {format_price(listing.all_in_price)} "
        f"(Price {format_price(listing.price)} + Shipping {format_price(listing.shipping)})"
    )
    if listing.condition:
        st.write(f"**Condition:** {listing.condition}")
    if listing.location:
        st.write(f"**Location:** {listing.location}")
    if listing.deal_score is not None:
        st.write(
            f"**Deal score:** {listing.deal_score:.1f} "
            f"(Confidence: {listing.deal_confidence})"
        )
    else:
        st.write("**Deal score:** Not enough data yet.")
    st.caption("Deal Score uses item price only; shipping excluded.")

    with st.expander("Why this score?"):
        st.write(f"**Listing price used:** {format_price(listing.price)} (price only)")
        st.write(
            f"**Reference (median) price:** {format_price(listing.deal_reference_price)}"
        )
        st.write(
            f"**Percent difference:** {format_percent(listing.deal_percent_diff)} vs median"
        )
        confidence_label = listing.deal_confidence or "unknown"
        reasons = listing.deal_confidence_reasons or ["no confidence data"]
        st.write(f"**Confidence:** {confidence_label}")
        st.write("**Confidence reasons:** " + ", ".join(reasons))
    st.markdown(f"[View listing]({listing.url})")
    st.divider()


def search_page() -> None:
    """Render the search page."""

    st.title("FretScout")
    st.write("Discover used & vintage guitars. Click out to buy on source sites.")
    client_id = get_secret("EBAY_CLIENT_ID")
    client_secret = get_secret("EBAY_CLIENT_SECRET")
    demo_mode = not client_id or not client_secret
    if demo_mode:
        st.info("eBay live search is not configured on this deployment yet.")

    category_options = {
        "All guitars & basses": 3858,
        "Electric guitars": 33034,
        "Acoustic guitars": 33021,
        "Bass guitars": 4713,
    }
    selected_category = st.sidebar.selectbox("Category", list(category_options.keys()))
    category_id = category_options.get(selected_category)

    query = st.text_input("Search used/vintage listings", placeholder="e.g. Fender Stratocaster")
    max_price = st.number_input("Max price (optional)", min_value=0.0, value=0.0, step=50.0)

    max_price_value = max_price if max_price > 0 else None
    if st.button("Save alert", type="primary", use_container_width=True):
        if query.strip():
            alert_service.save_alert(st.session_state.connection, query, max_price_value)
            st.success("Alert saved.")
        else:
            st.warning("Enter a search query before saving an alert.")

    if st.button("Search listings", use_container_width=True):
        if not query.strip():
            st.warning("Enter a search query to see results.")
            return

        if demo_mode:
            st.warning("Showing demo listings while eBay search is unavailable.")
            listings = stub_connector.fetch_listings(query)
        else:
            try:
                listings = ebay_source.search_ebay_listings(
                    query,
                    category_ids=[category_id] if category_id else None,
                    max_price=max_price_value,
                )
            except Exception as exc:  # pragma: no cover - UI guardrail
                st.error(f"eBay search failed; showing sample listings. ({exc})")
                listings = stub_connector.fetch_listings(query)

        listings = ensure_listing_ids(listings)
        listings = dedupe_listings(listings)

        if max_price_value is not None:
            listings = [
                listing
                for listing in listings
                if listing.all_in_price is not None
                and listing.all_in_price <= max_price_value
            ]
        listings = score_listings(listings)
        st.session_state.listings = listings
        st.session_state.query = query

        alerts = alert_service.list_saved_alerts(st.session_state.connection)
        alert_service.generate_alert_events(
            st.session_state.connection, alerts=alerts, listings=listings
        )

    if "listings" in st.session_state:
        st.sidebar.subheader("Results")
        sort_mode = st.sidebar.selectbox(
            "Sort by",
            ["Relevance", "Price (low→high)", "Deal Score (best→worst)"],
        )
        min_score = st.sidebar.slider("Min Deal Score", 0, 100, 0)
        high_conf_only = st.sidebar.checkbox("High confidence only", value=False)

        listings = st.session_state.listings
        listings = filter_listings(
            listings,
            min_score=min_score,
            high_conf_only=high_conf_only,
        )
        listings = sort_listings(listings, sort_mode=sort_mode)
        if listings:
            st.write(f"Found {len(listings)} listing(s).")
            for listing in listings:
                render_listing(listing)
        else:
            st.info("No listings found for this query.")


def alerts_page() -> None:
    """Render the alerts page."""

    st.title("Alerts")
    alerts = alert_service.list_saved_alerts(st.session_state.connection)
    events = alert_service.list_alert_events(st.session_state.connection)

    st.subheader("Saved alerts")
    if alerts:
        for alert in alerts:
            st.write(
                f"**{alert.query}** | Max price: {format_price(alert.max_price)} "
                f"| Created: {alert.created_at}"
            )
    else:
        st.info("No saved alerts yet.")

    st.subheader("Alert events")
    if events:
        for event in events:
            st.write(
                f"Alert #{event.alert_id} | {event.message} | {event.created_at}"
            )
    else:
        st.info("No alert events yet.")


def main() -> None:
    """Run the Streamlit app."""

    if "connection" not in st.session_state:
        st.session_state.connection = initialize_database()

    page = st.sidebar.selectbox("Navigate", ["Search", "Alerts"])
    if page == "Search":
        search_page()
    else:
        alerts_page()


if __name__ == "__main__":
    main()
