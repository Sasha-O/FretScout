"""Configuration helpers for FretScout."""

from __future__ import annotations

from typing import Optional

import os


def get_secret(name: str) -> Optional[str]:
    """Return a secret value from environment or Streamlit secrets."""

    value = os.environ.get(name)
    if value:
        return value

    try:
        import streamlit as st
    except ModuleNotFoundError:
        return None

    try:
        return st.secrets.get(name)
    except Exception:
        return None
