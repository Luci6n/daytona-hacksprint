"""Shared AnalysisResult contract — must match DaddyFix/Models/AnalysisResult.swift."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ARAnnotation(BaseModel):
    type: str = Field(description="highlight | arrow | circle | text")
    x: float = Field(ge=0.0, le=1.0, description="Normalized 0-1, top-left origin")
    y: float = Field(ge=0.0, le=1.0)
    z: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    label: str
    color: Optional[str] = None


class RepairStep(BaseModel):
    step: int
    instruction: str
    safetyNote: Optional[str] = None


class BuyablePart(BaseModel):
    id: str
    name: str
    estimatedPrice: str
    x402Ready: bool = False


class AnalysisResult(BaseModel):
    detectedItem: str
    confidence: float
    issues: list[str]
    arAnnotations: list[ARAnnotation]
    repairSteps: list[RepairStep]
    buyableParts: list[BuyablePart]
    # Optional live-stream metadata (ignored by older clients if absent — we always can omit)
    sessionId: Optional[str] = None
    seq: Optional[int] = None
    eventType: Optional[str] = None  # "snapshot" | "live" | "rtsp"


class AnalyzeRequest(BaseModel):
    """iOS can POST JSON with base64 image, or multipart file via /analyze."""

    imageBase64: Optional[str] = None
    mimeType: str = "image/jpeg"
    hint: Optional[str] = "Rinnai tankless water heater / home repair"


class StreamStartRTSPRequest(BaseModel):
    """Start continuous analysis by sampling an RTSP camera URL on Daytona."""

    rtspUrl: str = Field(description="rtsp://user:pass@host:554/stream")
    hint: Optional[str] = "Detect leaks, drips, flowing water, trip events over time"
    intervalSec: float = 2.0
    sessionId: Optional[str] = None


class StreamStartPhoneRequest(BaseModel):
    hint: Optional[str] = None
    sessionId: Optional[str] = None


class StreamPhoneEventRequest(BaseModel):
    """Phone-side live event (Brian) — same agent path as RTSP samples."""

    sessionId: str
    imageBase64: str
    mimeType: str = "image/jpeg"
    seq: Optional[int] = None
    hint: Optional[str] = None
