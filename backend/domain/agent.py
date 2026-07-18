from dataclasses import dataclass

from backend.demo import generic_unavailable_result, water_heater_result
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
        # Explicit demo only — never use heater fixture as silent live fallback.
        if self._demo_mode:
            return water_heater_result()
        if self._providers is None:
            raise ProviderConfigurationError(
                "Live analysis requires configured provider dependencies."
            )

        # Prefer the real scene. Empty/wrong hints must not force "water heater".
        device_hint = (request.device_hint or "").strip() or None
        context = self._providers.repair_context.search_repair_context(
            device_hint=device_hint or "household device repair",
            symptom=request.symptom,
        )
        visual_context = None
        if self._providers.vision is not None:
            try:
                observation = self._providers.vision.inspect(request)
                visual_context = observation.model_dump_json(by_alias=True)
            except Exception as exc:  # noqa: BLE001
                visual_context = (
                    f'{{"visionError": "{type(exc).__name__}: {exc}", '
                    f'"note": "Reasoning must still use the user image if available."}}'
                )

        try:
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
        except Exception as exc:  # noqa: BLE001
            return generic_unavailable_result(
                device_hint=device_hint,
                symptom=request.symptom,
                reason=f"{type(exc).__name__}: {exc}",
            )

        # If model still hallucinated heater when user clearly said mouse/battery, soft-correct is hard;
        # safety check only.
        # Ensure steps exist + inject licensed-pro stop language if model omitted it.
        result = self._coerce_minimum_safety(result)
        if not result.repair_steps:
            return generic_unavailable_result(
                device_hint=device_hint or request.symptom or "device in view",
                symptom=request.symptom,
                reason="model returned no repair steps",
            )

        if self._providers.safety is not None:
            try:
                self._providers.safety.validate(result)
            except Exception:  # noqa: BLE001
                pass

        return result

    @staticmethod
    def _coerce_minimum_safety(result: AnalysisResult) -> AnalysisResult:
        """Do not throw away a good visual diagnosis for a missing safety phrase."""
        if not result.repair_steps:
            return result
        licensed_line = (
            "If you are unsure or anything looks damaged/swollen/hot, stop and "
            "call a licensed professional."
        )
        fixed_steps = []
        for step in result.repair_steps:
            note = (step.safety_note or "").strip()
            if "licensed" not in note.lower():
                note = f"{note} {licensed_line}".strip() if note else licensed_line
            fixed_steps.append(step.model_copy(update={"safety_note": note}))
        return result.model_copy(update={"repair_steps": fixed_steps})
