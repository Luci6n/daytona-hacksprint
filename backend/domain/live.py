from dataclasses import dataclass

from backend.models import AnalysisResult, AnalyzeRequest


@dataclass
class LiveSessionState:
    """Conversation state owned by one live-camera WebSocket connection."""

    session_id: str
    latest_image_base64: str | None = None
    device_hint: str | None = None
    previous_analysis: AnalysisResult | None = None

    def accept_frame(self, image_base64: str, device_hint: str | None) -> None:
        self.latest_image_base64 = image_base64
        if device_hint is not None:
            self.device_hint = device_hint

    def analysis_request(self, utterance: str) -> AnalyzeRequest:
        if self.latest_image_base64 is None:
            raise ValueError("Send a frame before asking DaddyFix a question.")
        return AnalyzeRequest(
            symptom=utterance,
            device_hint=self.device_hint,
            image_base64=self.latest_image_base64,
        )

    def conversation_context(self) -> str | None:
        if self.previous_analysis is None:
            return None
        return self.previous_analysis.model_dump_json(by_alias=True)
