"""Oxylabs product / parts scrape — stub for hackathon (wire credentials later)."""

from __future__ import annotations

import os
from typing import Any


def is_configured() -> bool:
    return bool(os.getenv("OXYLABS_USERNAME") and os.getenv("OXYLABS_PASSWORD"))


def scrape_parts(query: str) -> list[dict[str, Any]]:
    """Return empty list until Oxylabs is configured."""
    if not is_configured():
        return []
    # TODO: Lucian/engineer — real Oxylabs realtime crawler call
    _ = query
    return []
