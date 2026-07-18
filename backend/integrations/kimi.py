from openai import OpenAI
from openai.types.chat import (
    ChatCompletionContentPartParam,
    ChatCompletionMessageParam,
)

from backend.config import Settings
from backend.models import AnalysisResult, AnalyzeRequest
from backend.provider_errors import ProviderConfigurationError, ProviderResponseError


SYSTEM_PROMPT = """You are DaddyFix, a safety-first spatial home repair vision agent.

You analyze the ACTUAL image and user symptom. Do NOT invent a water heater,
ELCB, or any device that is not visible in the image or clearly described.

Return JSON only matching the supplied schema exactly.
Coordinates x,y are NORMALIZED 0..1 with origin at the TOP-LEFT of the image.
Place arAnnotations ON the real broken/missing/relevant part (e.g. empty battery
compartment, missing battery, cracked housing, loose cable, tripped breaker).

Annotation rules:
- type "highlight" for the problem region (battery bay, empty slot, damage)
- type "arrow" pointing at that region
- type "text" with a short label (e.g. "Battery missing", "Insert AA here")
- label should name the part simply
- color soft green/teal when helpful: #22C55E, #38BDF8

Repair rules:
- 2-4 short steps that match WHAT IS ACTUALLY WRONG
- Every repairSteps[].safetyNote must be non-empty and mention calling a
  licensed professional when unsure or if the fix is electrical/gas/high-risk
- For a wireless mouse/keyboard with no battery: highlight the open battery
  compartment and steps to insert the correct cells (polarity, size)
- Never invent Rinnai/ELCB unless the image clearly shows a water heater panel
- buyableParts: only parts that match the diagnosis (e.g. AA/AAA batteries)

If the image is unclear, say so with low confidence and still return valid JSON.
"""


class KimiReasoningClient:
    """OpenAI-compatible reasoning adapter for Moonshot or ai&-hosted Kimi."""

    def __init__(self, settings: Settings) -> None:
        if settings.aiand_api_key and settings.aiand_base_url and settings.aiand_model:
            api_key = settings.aiand_api_key
            base_url = settings.aiand_base_url
            self._model = settings.aiand_model
            # Prefer multimodal when an image is present; many gateways accept
            # image_url. Text-only models will error and the agent may retry.
            self._supports_vision = True
            self._provider = "aiand"
        elif settings.moonshot_api_key:
            api_key = settings.moonshot_api_key
            base_url = settings.kimi_base_url
            self._model = settings.kimi_model
            self._supports_vision = True
            self._provider = "moonshot"
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
        if not request.image_base64 and not visual_context:
            raise ValueError(
                "imageBase64 (or a prior visual observation) is required for live analysis."
            )

        schema = AnalysisResult.model_json_schema(by_alias=True)
        user_text = (
            "Analyze the real scene. Do not default to a water heater.\n"
            f"Device hint (may be empty/wrong): {request.device_hint or 'none — trust the image'}\n"
            f"Reported symptom: {request.symptom or 'not provided — infer from image'}\n"
            f"Vision model observation JSON: {visual_context or 'none'}\n"
            f"Previous turn context: {conversation_context or 'No previous turn'}\n"
            f"Web/product context (may be empty): {repair_context}\n"
            f"Required JSON schema: {schema}\n"
            "Return arAnnotations that mark the exact problem area in the image "
            "(e.g. empty battery compartment on a mouse)."
        )

        # Always attach image when present so the model can see the mouse/device.
        user_content: str | list[ChatCompletionContentPartParam]
        if request.image_base64:
            image_url = request.image_base64
            if not image_url.startswith("data:"):
                image_url = f"data:image/jpeg;base64,{image_url}"
            user_content = [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
        else:
            user_content = user_text

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,
            )
        except Exception as exc:
            # Text-only models: retry without image_url if multimodal rejected
            if request.image_base64 and visual_context:
                try:
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": user_text
                            + "\n(Image could not be sent; use vision observation only.)",
                        },
                    ]
                    response = self._client.chat.completions.create(
                        model=self._model,
                        messages=messages,
                        response_format={"type": "json_object"},
                        temperature=0.1,
                    )
                except Exception as exc2:
                    raise ProviderResponseError(
                        f"Kimi request failed: {exc2}"
                    ) from exc2
            else:
                raise ProviderResponseError(f"Kimi request failed: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise ProviderResponseError("Kimi returned an empty response.")
        try:
            return AnalysisResult.model_validate_json(content)
        except ValueError as exc:
            raise ProviderResponseError(
                "Kimi returned JSON that does not match AnalysisResult."
            ) from exc
