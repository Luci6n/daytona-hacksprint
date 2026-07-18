from dataclasses import dataclass

from backend.demo import water_heater_result
from backend.domain.ports import (
    ReasoningProvider,
    RepairContextProvider,
    SafetyProvider,
    VisionProvider,
)
from backend.models import AnalysisResult, AnalyzeRequest
from backend.provider_errors import ProviderConfigurationError, UnsafeGuidanceError


@dataclass(frozen=True)
class AgentProviders:
    repair_context: RepairContextProvider
    reasoning: ReasoningProvider
    vision: VisionProvider | None = None
    safety: SafetyProvider | None = None


class DaddyAgent:
    def __init__(
        self,
        demo_mode: bool,
        providers: AgentProviders | None = None,
    ) -> None:
        self._demo_mode = demo_mode
        self._providers = providers

    def analyze(
        self,
        request: AnalyzeRequest,
        conversation_context: str | None = None,
    ) -> AnalysisResult:
        if self._demo_mode:
            return water_heater_result()
        if self._providers is None:
            raise ProviderConfigurationError(
                "Live analysis requires configured provider dependencies."
            )

        device_hint = request.device_hint or "Rinnai tankless water heater"
        context = self._providers.repair_context.search_repair_context(
            device_hint=device_hint,
            symptom=request.symptom,
        )
        visual_context = None
        if self._providers.vision is not None:
            observation = self._providers.vision.inspect(request)
            visual_context = observation.model_dump_json(by_alias=True)

        if conversation_context is None:
            result = self._providers.reasoning.analyze(
                request,
                context,
                visual_context=visual_context,
            )
        else:
            result = self._providers.reasoning.analyze(
                request,
                context,
                visual_context=visual_context,
                conversation_context=conversation_context,
            )

        self._ensure_minimum_safety(result)

        if self._providers.safety is not None:
            verdict = self._providers.safety.validate(result)
            if not verdict.approved:
                concerns = "; ".join(verdict.concerns) or "unspecified safety concern"
                raise UnsafeGuidanceError(
                    f"Safety validation rejected repair guidance: {concerns}"
                )

        return result

    @staticmethod
    def _ensure_minimum_safety(result: AnalysisResult) -> None:
        if not result.repair_steps:
            raise UnsafeGuidanceError(
                "Safety validation rejected repair guidance without repair steps."
            )
        if not any(
            "licensed " in step.safety_note.lower() for step in result.repair_steps
        ):
            raise UnsafeGuidanceError(
                "Safety validation requires a licensed professional stop condition."
            )
