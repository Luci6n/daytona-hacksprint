from backend.config import Settings
from backend.domain.agent import AgentProviders, DaddyAgent
from backend.integrations.doubleword import (
    DoublewordSafetyClient,
    DoublewordVisionClient,
)
from backend.integrations.kimi import KimiReasoningClient
from backend.integrations.nosana import NosanaSpeechClient
from backend.integrations.oxylabs import OxylabsClient


def build_agent(settings: Settings) -> DaddyAgent:
    if settings.demo_mode:
        return DaddyAgent(demo_mode=True)

    vision = None
    if settings.aiand_api_key:
        vision = DoublewordVisionClient(settings)
    safety = None
    if settings.doubleword_api_key:
        safety = DoublewordSafetyClient(settings)

    return DaddyAgent(
        demo_mode=False,
        providers=AgentProviders(
            repair_context=OxylabsClient(settings),
            reasoning=KimiReasoningClient(settings),
            vision=vision,
            safety=safety,
        ),
    )


def build_speech_synthesizer(settings: Settings) -> NosanaSpeechClient:
    return NosanaSpeechClient(settings)
