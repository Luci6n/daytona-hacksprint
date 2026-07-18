"""Shared AnalysisResult contract — must match DaddyFix/Models/AnalysisResult.swift."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ARAnnotation(BaseModel):
    type: str = Field(description='highlight | arrow | circle | text')
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


class AnalyzeRequest(BaseModel):
    """iOS can POST JSON with base64 image, or multipart file via /analyze."""

    imageBase64: Optional[str] = None
    mimeType: str = "image/jpeg"
    hint: Optional[str] = "Rinnai tankless water heater / home repair"
