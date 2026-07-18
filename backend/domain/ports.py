from typing import Protocol

from pydantic import BaseModel

from backend.models import AnalysisResult, AnalyzeRequest, VisionObservation


class SafetyVerdict(BaseModel):
    approved: bool
    concerns: list[str]


class RepairContextProvider(Protocol):
    def search_repair_context(
        self, device_hint: str, symptom: str | None
    ) -> str: ...


class VisionProvider(Protocol):
    def inspect(self, request: AnalyzeRequest) -> VisionObservation: ...


class ReasoningProvider(Protocol):
    def analyze(
        self,
        request: AnalyzeRequest,
        repair_context: str,
        visual_context: str | None = None,
    ) -> AnalysisResult: ...


class SafetyProvider(Protocol):
    def validate(self, result: AnalysisResult) -> SafetyVerdict: ...


class SpeechSynthesizer(Protocol):
    def synthesize(self, text: str) -> bytes: ...
