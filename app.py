"""Streamlit application for FretScout MVP."""

from __future__ import annotations

from typing import Optional

import streamlit as st

from fretscout import alerts as alert_service
from fretscout.connectors import stub as stub_connector
from fretscout.db import initialize_database


def format_price(value: Optional[float]) -> str:
    """Format a numeric value as a price string."""

    if value is None:
        return "N/A"
    return f"${value:,.2f}"


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
    st.markdown(f"[View listing]({listing.url})")
    st.divider()


def search_page() -> None:
    """Render the search page."""

    st.title("FretScout")
    st.write("Discover used & vintage guitars. Click out to buy on source sites.")

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

        listings = stub_connector.fetch_listings(query)
        if max_price_value is not None:
            listings = [
                listing
                for listing in listings
                if listing.all_in_price <= max_price_value
            ]
        st.session_state.listings = listings
        st.session_state.query = query

        alerts = alert_service.list_saved_alerts(st.session_state.connection)
        alert_service.generate_alert_events(
            st.session_state.connection, alerts=alerts, listings=listings
        )

    if "listings" in st.session_state:
        listings = st.session_state.listings
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
