"""
Nosana — decentralized GPU compute (cloud).

iOS never talks to Nosana directly. Only the agent inside the Daytona sandbox does.
Wire real job submit when NOSANA_API_KEY / endpoint is available.
"""

from __future__ import annotations

import os
from typing import Any


def is_configured() -> bool:
    return bool(os.getenv("NOSANA_API_KEY") or os.getenv("NOSANA_ENDPOINT"))


def submit_vision_job(image_base64: str, mime_type: str = "image/jpeg") -> dict[str, Any] | None:
    """
    Optional heavy vision path on Nosana GPU.

    Returns job result payload or None if not configured / skipped.
    For the hackathon, primary vision is Kimi from the Daytona sandbox;
    Nosana is the upgrade path for heavier models.
    """
    if not is_configured():
        return None
    # TODO: engineer — submit Nosana job, poll result
    _ = (image_base64, mime_type)
    return None
