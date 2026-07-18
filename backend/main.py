"""
DaddyFix FastAPI — Daytona cloud agent.

  One-shot:  POST /analyze
  Mock:      GET  /analyze/mock
  Live RTSP: POST /stream/rtsp/start  → samples camera every N sec → Kimi
  Live phone:POST /stream/phone/event → iOS frame events
  Latest:    GET  /stream/{sessionId}/latest  → iOS AR refresh

iOS never holds Kimi/Oxylabs/Nosana keys — only this public base URL.
"""

from __future__ import annotations

import base64
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from daddy_agent import demo_mock, run_analysis
from models import (
    AnalysisResult,
    AnalyzeRequest,
    StreamPhoneEventRequest,
    StreamStartPhoneRequest,
    StreamStartRTSPRequest,
)
from rtsp_ingest import ffmpeg_available
from stream_session import manager

load_dotenv()

app = FastAPI(title="DaddyFix Agent API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "visionMode": os.getenv("VISION_MODE", "mock"),
        "model": os.getenv("KIMI_MODEL", "kimi-k2.7-code"),
        "hasMoonshotKey": bool(os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")),
        "ffmpeg": ffmpeg_available(),
        "rtspReady": ffmpeg_available(),
        "features": ["analyze", "analyze/mock", "stream/rtsp", "stream/phone"],
    }


@app.get("/analyze/mock", response_model=AnalysisResult)
def analyze_mock() -> AnalysisResult:
    return demo_mock()


@app.post("/analyze", response_model=AnalysisResult)
async def analyze_json(body: AnalyzeRequest) -> AnalysisResult:
    return run_analysis(
        image_base64=body.imageBase64,
        mime_type=body.mimeType,
        hint=body.hint,
        force_mock=False,
    )


@app.post("/analyze/upload", response_model=AnalysisResult)
async def analyze_upload(
    file: UploadFile = File(...),
    hint: Optional[str] = Form(None),
    force_mock: bool = Form(False),
) -> AnalysisResult:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    b64 = base64.b64encode(raw).decode("ascii")
    mime = file.content_type or "image/jpeg"
    return run_analysis(
        image_base64=b64,
        mime_type=mime,
        hint=hint,
        force_mock=force_mock,
    )


# ── Live continuous events ───────────────────────────────────────────


@app.post("/stream/rtsp/start")
def stream_rtsp_start(body: StreamStartRTSPRequest) -> dict:
    """
    Start sampling an RTSP URL on the server (IP camera / NVR / MediaMTX).

    Use this when a single screenshot cannot show a temporal event (leak, drip).
    Agent pulls frames every intervalSec; iOS polls /stream/{id}/latest for AR.
    """
    if not body.rtspUrl.startswith("rtsp://") and not body.rtspUrl.startswith("rtsps://"):
        raise HTTPException(status_code=400, detail="rtspUrl must start with rtsp:// or rtsps://")
    session = manager.start_rtsp(
        body.rtspUrl,
        hint=body.hint,
        interval_sec=body.intervalSec,
        session_id=body.sessionId,
    )
    return {
        "ok": True,
        "sessionId": session.session_id,
        "source": "rtsp",
        "intervalSec": session.interval_sec,
        "pollUrl": f"/stream/{session.session_id}/latest",
        "statusUrl": f"/stream/{session.session_id}/status",
        "note": "Install ffmpeg in Daytona if /health.ffmpeg is false",
    }


@app.post("/stream/phone/start")
def stream_phone_start(body: StreamStartPhoneRequest) -> dict:
    """Open a phone-driven live session; client then POSTs /stream/phone/event."""
    session = manager.start_phone(hint=body.hint, session_id=body.sessionId)
    return {
        "ok": True,
        "sessionId": session.session_id,
        "source": "phone",
        "eventUrl": "/stream/phone/event",
        "pollUrl": f"/stream/{session.session_id}/latest",
    }


@app.post("/stream/phone/event", response_model=AnalysisResult)
def stream_phone_event(body: StreamPhoneEventRequest) -> AnalysisResult:
    """Brian iOS: one live frame event → same Daddy Agent as RTSP samples."""
    if not body.imageBase64:
        raise HTTPException(status_code=400, detail="imageBase64 required")
    result = manager.ingest_phone_frame(
        body.sessionId,
        body.imageBase64,
        mime_type=body.mimeType,
        hint=body.hint,
        seq=body.seq,
    )
    # Attach live metadata for clients that want it
    return result.model_copy(
        update={
            "sessionId": body.sessionId,
            "seq": body.seq,
            "eventType": "live",
        }
    )


@app.get("/stream/{session_id}/latest", response_model=AnalysisResult)
def stream_latest(session_id: str) -> AnalysisResult:
    session = manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Unknown sessionId")
    if not session.last_result:
        raise HTTPException(
            status_code=404,
            detail=session.last_error or "No analysis yet — wait for first frame",
        )
    return session.last_result.model_copy(
        update={
            "sessionId": session.session_id,
            "seq": session.seq,
            "eventType": "rtsp" if session.source == "rtsp" else "live",
        }
    )


@app.get("/stream/{session_id}/status")
def stream_status(session_id: str) -> dict:
    session = manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Unknown sessionId")
    return session.to_status()


@app.post("/stream/{session_id}/stop")
def stream_stop(session_id: str) -> dict:
    ok = manager.stop(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Unknown sessionId")
    return {"ok": True, "sessionId": session_id, "active": False}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
