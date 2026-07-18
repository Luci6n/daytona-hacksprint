from openai import OpenAI
from openai.types.chat import (
    ChatCompletionContentPartParam,
    ChatCompletionMessageParam,
)

from backend.config import Settings
from backend.models import AnalysisResult, AnalyzeRequest
from backend.provider_errors import ProviderConfigurationError, ProviderResponseError


# General-scene prompt (not water-heater-only). Lucian's ai& call params below.
SYSTEM_PROMPT = """You are DaddyFix, a safety-first spatial home repair vision agent.

Analyze the ACTUAL image and user symptom. Do NOT invent a water heater, ELCB,
or any device that is not visible in the image or clearly described by the user.

Return JSON only matching the supplied schema exactly.
Coordinates x,y are NORMALIZED 0..1 with origin at the TOP-LEFT of the image.
Place arAnnotations ON the real broken/missing/relevant part (e.g. empty battery
compartment, missing battery, cracked housing, loose cable, tripped breaker).

Annotation rules:
- type "highlight" for the problem region (battery bay, empty slot, damage)
- type "arrow" pointing at that region
- type "text" with a short label (e.g. "Battery missing", "Insert AA here")
- For a wireless mouse with no batteries: highlight the open battery compartment

Repair rules:
- 2-4 short steps that match WHAT IS ACTUALLY WRONG
- Every repairSteps[].safetyNote must be non-empty and tell the user to call a
  licensed professional when unsure or if the fix is electrical/gas/high-risk
- buyableParts must match the diagnosis (e.g. AA batteries for a mouse)
- Never invent Rinnai/ELCB unless the image clearly shows a water heater panel
- Set riskLevel to low, medium, high, or emergency based on the visible hazard
  and reported symptom. Gas, burning, flooding near electricity, and exposed
  live electrical conditions are high or emergency risk.

If the image is unclear, say so with low confidence and still return valid JSON.
"""


class KimiReasoningClient:
    """OpenAI-compatible reasoning adapter for Moonshot or ai& (Lucian-verified)."""

    def __init__(self, settings: Settings) -> None:
        if settings.aiand_api_key and settings.aiand_base_url and settings.aiand_model:
            api_key = settings.aiand_api_key
            base_url = settings.aiand_base_url
            self._model = settings.aiand_model
            # Lucian: ai& path is text-only; Doubleword supplies visual_context.
            self._supports_vision = False
            self._uses_aiand = True
        elif settings.moonshot_api_key:
            api_key = settings.moonshot_api_key
            base_url = settings.kimi_base_url
            self._model = settings.kimi_model
            self._supports_vision = True
            self._uses_aiand = False
        else:
            raise ProviderConfigurationError(
                "Kimi requires either MOONSHOT_API_KEY, or complete ai& settings "
                "(AIAND_API_KEY, AIAND_BASE_URL, AIAND_MODEL)."
            )
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def analyze(
        self,
        request: AnalyzeRequest,
        repair_context: str,
        visual_context: str | None = None,
        conversation_context: str | None = None,
    ) -> AnalysisResult:
        if self._supports_vision and not request.image_base64:
            raise ValueError("imageBase64 is required when DEMO_MODE=false.")
        if self._uses_aiand and not visual_context and not request.image_base64:
            raise ValueError(
                "ai& path needs Doubleword visual observation or an image context."
            )

        schema = AnalysisResult.model_json_schema(by_alias=True)
        user_text = (
            "Analyze the real scene. Prefer the image/observation over any prior.\n"
            f"Device hint (may be empty/wrong): {request.device_hint or 'none — trust vision'}\n"
            f"Reported symptom: {request.symptom or 'not provided — infer from vision'}\n"
            f"Verified visual observation JSON: {visual_context or 'none'}\n"
            f"Previous turn context: {conversation_context or 'No previous turn'}\n"
            f"Oxylabs repair context: {repair_context}\n"
            f"Required JSON schema: {schema}\n"
            "Return arAnnotations on the exact problem area "
            "(e.g. empty battery compartment on a mouse)."
        )
        user_content: str | list[ChatCompletionContentPartParam] = user_text
        if self._supports_vision and request.image_base64:
            image_url = request.image_base64
            if not image_url.startswith("data:"):
                image_url = f"data:image/jpeg;base64,{image_url}"
            user_content = [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
        try:
            # Lucian-verified ai& call shape (bba342e).
            if self._uses_aiand:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0,
                    max_completion_tokens=1_000,
                    extra_body={"reasoning_effort": "none"},
                )
            else:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )
        except Exception as exc:
            raise ProviderResponseError(f"Kimi request failed: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            # Some gateways put text in refusal / empty content with tool traces
            raise ProviderResponseError("Kimi returned an empty response.")
        try:
            return AnalysisResult.model_validate_json(content)
        except ValueError as exc:
            raise ProviderResponseError(
                "Kimi returned JSON that does not match AnalysisResult."
            ) from exc
