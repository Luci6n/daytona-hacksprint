"""
DaddyFix FastAPI — run in Daytona sandbox or locally.

  cd backend
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  cp .env.example .env   # set MOONSHOT_API_KEY
  uvicorn main:app --host 0.0.0.0 --port 8000

iOS VisionService → POST /analyze  → AnalysisResult JSON (camelCase)
"""

from __future__ import annotations

import base64
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from daddy_agent import demo_mock, run_analysis
from models import AnalysisResult, AnalyzeRequest

load_dotenv()

app = FastAPI(title="DaddyFix Agent API", version="0.1.0")

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
    }


@app.get("/analyze/mock", response_model=AnalysisResult)
def analyze_mock() -> AnalysisResult:
    """No image needed — hero demo payload for iOS / AR testing."""
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


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
