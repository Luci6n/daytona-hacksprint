from collections.abc import Callable

from fastapi import APIRouter, Response

from backend.config import Settings
from backend.domain.ports import AnalysisAgent, SpeechSynthesizer
from backend.models import AnalysisResult, AnalyzeRequest, SpeechRequest


AgentFactory = Callable[[], AnalysisAgent]
SpeechFactory = Callable[[], SpeechSynthesizer]


def create_router(
    settings: Settings,
    agent_factory: AgentFactory,
    speech_factory: SpeechFactory,
) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "service": "daddyfix-backend",
            "environment": settings.app_env,
            "demoMode": settings.demo_mode,
            "providers": settings.provider_readiness(),
        }

    @router.post("/analyze", response_model=AnalysisResult)
    def analyze(request: AnalyzeRequest) -> AnalysisResult:
        return agent_factory().analyze(request)

    @router.post("/speech/synthesize", response_class=Response)
    def synthesize_speech(request: SpeechRequest) -> Response:
        audio = speech_factory().synthesize(request.text)
        return Response(content=audio, media_type="audio/wav")

    return router
