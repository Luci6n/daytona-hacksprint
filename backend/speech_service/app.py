from io import BytesIO
import os
from threading import Lock

import soundfile as sf  # type: ignore[import-not-found]
import torch  # type: ignore[import-not-found]
from fastapi import FastAPI, Response
from pydantic import BaseModel, Field
from qwen_tts import Qwen3TTSModel  # type: ignore[import-not-found]


MODEL_ID = os.getenv(
    "TTS_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
)


class SynthesisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2_000)
    language: str = "English"
    instruct: str = Field(min_length=1, max_length=2_000)


app = FastAPI(title="DaddyFix Qwen3-TTS", version="0.1.0")
_model: Qwen3TTSModel | None = None
_model_lock = Lock()


def get_model() -> Qwen3TTSModel:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = Qwen3TTSModel.from_pretrained(
                    MODEL_ID,
                    device_map="cuda:0",
                    dtype=torch.bfloat16,
                    attn_implementation="sdpa",
                )
    return _model


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "model": MODEL_ID, "modelLoaded": _model is not None}


@app.post("/warmup")
def warmup() -> dict[str, str]:
    get_model()
    return {"status": "ready"}


@app.post("/synthesize", response_class=Response)
def synthesize(request: SynthesisRequest) -> Response:
    wavs, sample_rate = get_model().generate_voice_design(
        text=request.text,
        language=request.language,
        instruct=request.instruct,
    )
    buffer = BytesIO()
    sf.write(buffer, wavs[0], sample_rate, format="WAV")
    return Response(content=buffer.getvalue(), media_type="audio/wav")
