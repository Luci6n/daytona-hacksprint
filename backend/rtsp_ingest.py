"""
RTSP frame grab for continuous real-world events (leaks, motion, etc.).

Why RTSP:
  - Screenshots miss *change over time* (water dripping, valve moving).
  - RTSP is the standard "remote control + media path" for IP/CCTV cameras.
  - Daytona agent pulls frames on an interval → Kimi reasons → AnalysisResult.
  - iPhone LiDAR still places AR pins; it does not need to be the RTSP server.

Requires `ffmpeg` on PATH (install in Daytona sandbox / local machine).
"""

from __future__ import annotations

import base64
import shutil
import subprocess
import tempfile
from pathlib import Path


class RTSPIngestError(RuntimeError):
    pass


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def grab_jpeg_frame(
    rtsp_url: str,
    *,
    timeout_sec: float = 12.0,
    transport: str = "tcp",
) -> tuple[str, str]:
    """
    Pull a single JPEG frame from an RTSP URL via ffmpeg.

    Returns (base64_jpeg, mime_type="image/jpeg").
    Uses TCP transport by default (more reliable through firewalls).
    """
    if not ffmpeg_available():
        raise RTSPIngestError(
            "ffmpeg not found on PATH. Install ffmpeg in the Daytona sandbox "
            "(e.g. apt-get install -y ffmpeg) before using RTSP ingest."
        )
    if not rtsp_url or not rtsp_url.strip():
        raise RTSPIngestError("Empty RTSP URL")

    with tempfile.TemporaryDirectory(prefix="daddyfix-rtsp-") as tmp:
        out = Path(tmp) / "frame.jpg"
        # -rtsp_transport tcp: more stable than UDP on cloud networks
        # -frames:v 1: single snapshot from the live stream
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-rtsp_transport",
            transport,
            "-i",
            rtsp_url,
            "-frames:v",
            "1",
            "-q:v",
            "5",
            "-y",
            str(out),
        ]
        try:
            subprocess.run(
                cmd,
                check=True,
                timeout=timeout_sec,
                capture_output=True,
            )
        except subprocess.TimeoutExpired as exc:
            raise RTSPIngestError(f"RTSP grab timed out after {timeout_sec}s") from exc
        except subprocess.CalledProcessError as exc:
            err = (exc.stderr or b"").decode("utf-8", errors="replace")[:500]
            raise RTSPIngestError(f"ffmpeg failed: {err or exc}") from exc

        if not out.exists() or out.stat().st_size < 32:
            raise RTSPIngestError("ffmpeg produced empty frame")

        b64 = base64.b64encode(out.read_bytes()).decode("ascii")
        return b64, "image/jpeg"
