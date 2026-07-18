import pytest

from backend.demo import water_heater_result
from backend.domain.agent import AgentProviders, DaddyAgent
from backend.domain.ports import SafetyVerdict
from backend.models import AnalysisResult, AnalyzeRequest, RepairStep, VisionObservation
from backend.provider_errors import UnsafeGuidanceError


def test_live_agent_orchestrates_injected_providers_in_order() -> None:
    calls: list[str] = []
    expected = water_heater_result()

    class RepairContext:
        def search_repair_context(
            self, device_hint: str, symptom: str | None
        ) -> str:
            calls.append("repair")
            # Empty device_hint becomes a generic repair query (no forced water heater).
            assert device_hint == "household device repair"
            assert symptom == "No hot water"
            return "verified manual context"

    class Vision:
        def inspect(self, request: AnalyzeRequest) -> VisionObservation:
            calls.append("vision")
            return VisionObservation(
                detected_item="Rinnai tankless water heater",
                confidence=0.9,
                visible_issues=["ELCB appears tripped"],
                ar_annotations=[],
            )

    class Reasoning:
        def analyze(
            self,
            request: AnalyzeRequest,
            repair_context: str,
            visual_context: str | None = None,
            conversation_context: str | None = None,
        ) -> AnalysisResult:
            calls.append("reasoning")
            assert repair_context == "verified manual context"
            assert visual_context is not None
            assert "ELCB appears tripped" in visual_context
            assert conversation_context is None
            return expected

    class Safety:
        def validate(self, result: AnalysisResult) -> SafetyVerdict:
            calls.append("safety")
            assert result == expected
            return SafetyVerdict(approved=True, concerns=[])

    agent = DaddyAgent(
        demo_mode=False,
        providers=AgentProviders(
            repair_context=RepairContext(),
            reasoning=Reasoning(),
            vision=Vision(),
            safety=Safety(),
        ),
    )

    result = agent.analyze(AnalyzeRequest(symptom="No hot water"))

    assert result == expected
    assert calls == ["repair", "vision", "reasoning", "safety"]


def test_demo_agent_does_not_require_provider_dependencies() -> None:
    result = DaddyAgent(demo_mode=True).analyze(AnalyzeRequest())

    assert result.detected_item == "Rinnai Tankless Water Heater"


def test_live_agent_rejects_guidance_without_professional_stop_condition() -> None:
    class RepairContext:
        def search_repair_context(
            self, device_hint: str, symptom: str | None
        ) -> str:
            return "verified manual context"

    class Reasoning:
        def analyze(
            self,
            request: AnalyzeRequest,
            repair_context: str,
            visual_context: str | None = None,
            conversation_context: str | None = None,
        ) -> AnalysisResult:
            unsafe = water_heater_result()
            return unsafe.model_copy(
                update={
                    "repair_steps": [
                        RepairStep(
                            step=1,
                            instruction="Reset the breaker.",
                            safety_note="Turn off power before touching anything.",
                        )
                    ]
                }
            )

    agent = DaddyAgent(
        demo_mode=False,
        providers=AgentProviders(
            repair_context=RepairContext(),
            reasoning=Reasoning(),
        ),
    )

    # Safety notes without "licensed" are coerced onto the model result.
    result = agent.analyze(AnalyzeRequest(symptom="mouse has no battery"))
    assert result.repair_steps
    assert all("licensed" in s.safety_note.lower() for s in result.repair_steps)

def test_live_agent_rejects_negated_licensed_professional_note() -> None:
    class RepairContext:
        def search_repair_context(
            self, device_hint: str, symptom: str | None
        ) -> str:
            return "verified manual context"

    class Reasoning:
        def analyze(
            self,
            request: AnalyzeRequest,
            repair_context: str,
            visual_context: str | None = None,
            conversation_context: str | None = None,
        ) -> AnalysisResult:
            unsafe = water_heater_result()
            return unsafe.model_copy(
                update={
                    "repair_steps": [
                        RepairStep(
                            step=1,
                            instruction="Open the energized enclosure.",
                            safety_note=(
                                "You do not need a licensed professional for this."
                            ),
                        )
                    ]
                }
            )

    agent = DaddyAgent(
        demo_mode=False,
        providers=AgentProviders(
            repair_context=RepairContext(),
            reasoning=Reasoning(),
        ),
    )

    with pytest.raises(UnsafeGuidanceError, match="licensed professional"):
        agent.analyze(AnalyzeRequest(symptom="No hot water"))
