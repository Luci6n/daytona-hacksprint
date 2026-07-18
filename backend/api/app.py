from fastapi import FastAPI

from backend.api.errors import register_error_handlers
from backend.api.live import create_live_router
from backend.api.routes import AgentFactory, SpeechFactory, create_router
from backend.api.rtsp_routes import create_rtsp_router
from backend.bootstrap import build_agent, build_speech_synthesizer
from backend.config import Settings


def create_app(
    settings: Settings,
    agent_factory: AgentFactory | None = None,
    speech_factory: SpeechFactory | None = None,
) -> FastAPI:
    resolved_agent_factory = agent_factory or (lambda: build_agent(settings))
    resolved_speech_factory = speech_factory or (
        lambda: build_speech_synthesizer(settings)
    )
    app = FastAPI(
        title="DaddyFix Agent API",
        version="0.4.0",
        description="Safety-first spatial repair analysis for the DaddyFix iOS app.",
    )
    register_error_handlers(app)
    app.include_router(
        create_router(settings, resolved_agent_factory, resolved_speech_factory)
    )
    app.include_router(
        create_live_router(resolved_agent_factory, resolved_speech_factory)
    )
    # Continuous CCTV path: sample RTSP every 1–2s → same DaddyAgent
    app.include_router(create_rtsp_router(resolved_agent_factory))
    return app
