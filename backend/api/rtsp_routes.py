"""
RTSP continuous sampling — server pulls IP camera every N seconds,
runs DaddyAgent.analyze, stores latest AnalysisResult for the iPhone.

This is Path A continuous events (CCTV). Path B is phone WS /live/{id}.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import Field

from backend.domain.ports import AnalysisAgent
from backend.integrations.rtsp import RTSPError, ffmpeg_available, grab_jpeg_data_url
from backend.models import APIModel, AnalysisResult, AnalyzeRequest

AgentFactory = Callable[[], AnalysisAgent]


class RTSPStartRequest(APIModel):
    rtsp_url: str = Field(min_length=8, max_length=2_000)
    interval_sec: float = Field(default=2.0, ge=1.0, le=10.0)
    symptom: str | None = Field(
        default=(
            "Continuously monitor this camera. Report active leaks, drips, "
            "failures, or hazards and safe next steps."
        ),
        max_length=2_000,
    )
    device_hint: str | None = Field(default=None, max_length=500)
    session_id: str | None = Field(default=None, max_length=100)


@dataclass
class _RTSPSession:
    session_id: str
    rtsp_url: str
    interval_sec: float
    symptom: str
    device_hint: str | None
    stop: threading.Event = field(default_factory=threading.Event)
    seq: int = 0
    last_result: AnalysisResult | None = None
    last_error: str | None = None
    last_at: float | None = None
    active: bool = True
    thread: threading.Thread | None = None


_sessions: dict[str, _RTSPSession] = {}
_lock = threading.Lock()


def create_rtsp_router(agent_factory: AgentFactory) -> APIRouter:
    router = APIRouter(prefix="/rtsp", tags=["rtsp"])

    @router.get("/status")
    def rtsp_status() -> dict[str, Any]:
        return {
            "ffmpeg": ffmpeg_available(),
            "activeSessions": sum(1 for s in _sessions.values() if s.active),
        }

    @router.post("/start")
    def rtsp_start(body: RTSPStartRequest) -> dict[str, Any]:
        sid = body.session_id or uuid.uuid4().hex
        session = _RTSPSession(
            session_id=sid,
            rtsp_url=body.rtsp_url,
            interval_sec=body.interval_sec,
            symptom=body.symptom
            or "Continuously monitor this camera for leaks and hazards.",
            device_hint=body.device_hint,
        )

        with _lock:
            old = _sessions.get(sid)
            if old:
                old.active = False
                old.stop.set()
            _sessions[sid] = session

        def loop() -> None:
            agent = agent_factory()
            while not session.stop.is_set() and session.active:
                try:
                    data_url = grab_jpeg_data_url(session.rtsp_url)
                    request = AnalyzeRequest(
                        symptom=session.symptom,
                        device_hint=session.device_hint,
                        image_base64=data_url,
                    )
                    result = agent.analyze(request)
                    with _lock:
                        session.seq += 1
                        session.last_result = result
                        session.last_error = None
                        session.last_at = time.time()
                except (RTSPError, Exception) as exc:  # noqa: BLE001
                    with _lock:
                        session.last_error = f"{type(exc).__name__}: {exc}"
                session.stop.wait(session.interval_sec)
            with _lock:
                session.active = False

        t = threading.Thread(target=loop, name=f"rtsp-{sid[:8]}", daemon=True)
        session.thread = t
        t.start()

        return {
            "ok": True,
            "sessionId": sid,
            "intervalSec": session.interval_sec,
            "ffmpeg": ffmpeg_available(),
            "latestUrl": f"/rtsp/{sid}/latest",
            "statusUrl": f"/rtsp/{sid}/status",
            "stopUrl": f"/rtsp/{sid}/stop",
        }

    @router.get("/{session_id}/latest", response_model=AnalysisResult)
    def rtsp_latest(session_id: str) -> AnalysisResult:
        with _lock:
            session = _sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Unknown RTSP session")
            if session.last_result is None:
                detail = session.last_error or "No analysis yet — wait for first sample"
                raise HTTPException(status_code=404, detail=detail)
            return session.last_result

    @router.get("/{session_id}/status")
    def rtsp_session_status(session_id: str) -> dict[str, Any]:
        with _lock:
            session = _sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Unknown RTSP session")
            return {
                "sessionId": session.session_id,
                "active": session.active,
                "seq": session.seq,
                "intervalSec": session.interval_sec,
                "lastError": session.last_error,
                "lastAt": session.last_at,
                "hasResult": session.last_result is not None,
            }

    @router.post("/{session_id}/stop")
    def rtsp_stop(session_id: str) -> dict[str, Any]:
        with _lock:
            session = _sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Unknown RTSP session")
            session.active = False
            session.stop.set()
        return {"ok": True, "sessionId": session_id, "active": False}

    return router
