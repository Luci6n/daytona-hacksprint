"""RTSP frame grab via ffmpeg (server-side continuous sampling)."""

from __future__ import annotations

import base64
import shutil
import subprocess
import tempfile
from pathlib import Path


class RTSPError(RuntimeError):
    pass


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def grab_jpeg_data_url(rtsp_url: str, *, timeout_sec: float = 12.0) -> str:
    """
    Pull one JPEG from an RTSP URL and return a data URL for AnalyzeRequest.
    Requires ffmpeg on PATH (Daytona: apt-get install -y ffmpeg).
    """
    if not ffmpeg_available():
        raise RTSPError(
            "ffmpeg not found. Install ffmpeg in the Daytona sandbox to use RTSP sampling."
        )
    if not rtsp_url.startswith(("rtsp://", "rtsps://")):
        raise RTSPError("rtspUrl must start with rtsp:// or rtsps://")

    with tempfile.TemporaryDirectory(prefix="daddyfix-rtsp-") as tmp:
        out = Path(tmp) / "frame.jpg"
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-rtsp_transport",
            "tcp",
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
            subprocess.run(cmd, check=True, timeout=timeout_sec, capture_output=True)
        except subprocess.TimeoutExpired as exc:
            raise RTSPError(f"RTSP grab timed out after {timeout_sec}s") from exc
        except subprocess.CalledProcessError as exc:
            err = (exc.stderr or b"").decode("utf-8", errors="replace")[:400]
            raise RTSPError(f"ffmpeg failed: {err or exc}") from exc

        if not out.exists() or out.stat().st_size < 32:
            raise RTSPError("Empty frame from RTSP")

        b64 = base64.b64encode(out.read_bytes()).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"
