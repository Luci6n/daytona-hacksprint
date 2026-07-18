"""
Live analysis sessions — continuous events for the Daddy Agent.

Two ingest paths (same agent output: AnalysisResult):

1) RTSP (IP / CCTV camera) — server pulls stream on an interval (Lucian/Daytona).
2) Phone frame events — iOS POSTs JPEGs (Brian LiveAnalysisSession).

iOS polls GET /stream/{sessionId}/latest for AR updates, or uses the POST response.
"""

from __future__ import annotations

import asyncio
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from daddy_agent import run_analysis
from models import AnalysisResult
from rtsp_ingest import RTSPIngestError, grab_jpeg_frame


@dataclass
class StreamSession:
    session_id: str
    source: str  # "rtsp" | "phone"
    rtsp_url: Optional[str] = None
    hint: Optional[str] = None
    interval_sec: float = 2.0
    created_at: float = field(default_factory=time.time)
    active: bool = True
    seq: int = 0
    last_result: Optional[AnalysisResult] = None
    last_error: Optional[str] = None
    last_event_at: Optional[float] = None
    _stop: threading.Event = field(default_factory=threading.Event)
    _thread: Optional[threading.Thread] = None

    def to_status(self) -> dict[str, Any]:
        return {
            "sessionId": self.session_id,
            "source": self.source,
            "active": self.active,
            "seq": self.seq,
            "intervalSec": self.interval_sec,
            "rtspUrlSet": bool(self.rtsp_url),
            "hint": self.hint,
            "lastError": self.last_error,
            "lastEventAt": self.last_event_at,
            "hasResult": self.last_result is not None,
        }


class StreamSessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, StreamSession] = {}
        self._lock = threading.Lock()

    def get(self, session_id: str) -> Optional[StreamSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def start_rtsp(
        self,
        rtsp_url: str,
        *,
        hint: str | None = None,
        interval_sec: float = 2.0,
        session_id: str | None = None,
    ) -> StreamSession:
        sid = session_id or str(uuid.uuid4())
        session = StreamSession(
            session_id=sid,
            source="rtsp",
            rtsp_url=rtsp_url,
            hint=hint or "Watch for leaks, drips, motion, trip events",
            interval_sec=max(1.0, float(interval_sec)),
        )
        with self._lock:
            # stop existing with same id
            old = self._sessions.get(sid)
            if old:
                old.active = False
                old._stop.set()
            self._sessions[sid] = session

        t = threading.Thread(
            target=self._rtsp_loop,
            args=(session,),
            name=f"rtsp-{sid[:8]}",
            daemon=True,
        )
        session._thread = t
        t.start()
        return session

    def start_phone(
        self,
        *,
        hint: str | None = None,
        session_id: str | None = None,
    ) -> StreamSession:
        sid = session_id or str(uuid.uuid4())
        session = StreamSession(
            session_id=sid,
            source="phone",
            hint=hint,
            interval_sec=0.0,
        )
        with self._lock:
            self._sessions[sid] = session
        return session

    def stop(self, session_id: str) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            session.active = False
            session._stop.set()
            return True

    def ingest_phone_frame(
        self,
        session_id: str,
        image_base64: str,
        *,
        mime_type: str = "image/jpeg",
        hint: str | None = None,
        seq: int | None = None,
    ) -> AnalysisResult:
        session = self.get(session_id)
        if not session:
            # auto-create phone session
            session = self.start_phone(hint=hint, session_id=session_id)
        if not session.active and session.source == "phone":
            session.active = True

        result = run_analysis(
            image_base64=image_base64,
            mime_type=mime_type,
            hint=hint or session.hint,
            force_mock=False,
        )
        with self._lock:
            session.seq = seq if seq is not None else session.seq + 1
            session.last_result = result
            session.last_error = None
            session.last_event_at = time.time()
        return result

    def _rtsp_loop(self, session: StreamSession) -> None:
        """Background: sample RTSP → agent → store latest AnalysisResult."""
        while not session._stop.is_set() and session.active:
            try:
                assert session.rtsp_url
                b64, mime = grab_jpeg_frame(session.rtsp_url)
                result = run_analysis(
                    image_base64=b64,
                    mime_type=mime,
                    hint=session.hint,
                    force_mock=False,
                )
                with self._lock:
                    session.seq += 1
                    session.last_result = result
                    session.last_error = None
                    session.last_event_at = time.time()
            except RTSPIngestError as exc:
                with self._lock:
                    session.last_error = str(exc)
            except Exception as exc:  # noqa: BLE001
                with self._lock:
                    session.last_error = f"{type(exc).__name__}: {exc}"

            # wait interval (interruptible)
            session._stop.wait(session.interval_sec)

        with self._lock:
            session.active = False


# Process-wide manager (one FastAPI worker). Fine for hackathon.
manager = StreamSessionManager()
