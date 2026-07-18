from openai import OpenAI
from openai.types.chat import (
    ChatCompletionContentPartParam,
    ChatCompletionMessageParam,
)

from backend.config import Settings
from backend.models import AnalysisResult, AnalyzeRequest
from backend.provider_errors import ProviderConfigurationError, ProviderResponseError


SYSTEM_PROMPT = """You are DaddyFix, a safety-first home repair vision agent.
Return JSON only and follow the supplied JSON schema exactly.
Use normalized image coordinates from 0 to 1 with the origin at the top-left.
Never instruct users to perform gas work, open energized electrical enclosures,
or bypass safety equipment. Every repair step must include a safety note, and
uncertain or hazardous situations must tell the user to call a licensed professional.
For the hero scenario, identify a Rinnai tankless water heater and locate its ELCB.
"""


class KimiReasoningClient:
    """OpenAI-compatible reasoning adapter for Moonshot or ai&-hosted Kimi."""

    def __init__(self, settings: Settings) -> None:
        if settings.aiand_api_key and settings.aiand_base_url and settings.aiand_model:
            api_key = settings.aiand_api_key
            base_url = settings.aiand_base_url
            self._model = settings.aiand_model
            self._supports_vision = False
        elif settings.moonshot_api_key:
            api_key = settings.moonshot_api_key
            base_url = settings.kimi_base_url
            self._model = settings.kimi_model
            self._supports_vision = True
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

        schema = AnalysisResult.model_json_schema(by_alias=True)
        user_text = (
            f"Device hint: {request.device_hint or 'Rinnai tankless water heater'}\n"
            f"Reported symptom: {request.symptom or 'Not provided'}\n"
            f"Verified visual observation: {visual_context or 'Use the supplied image'}\n"
            f"Previous turn context: {conversation_context or 'No previous turn'}\n"
            f"Oxylabs repair context: {repair_context}\n"
            f"Required JSON schema: {schema}"
        )
        user_content: str | list[ChatCompletionContentPartParam] = user_text
        if self._supports_vision:
            image_url = request.image_base64 or ""
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
            raise ProviderResponseError("Kimi returned an empty response.")
        try:
            return AnalysisResult.model_validate_json(content)
        except ValueError as exc:
            raise ProviderResponseError(
                "Kimi returned JSON that does not match AnalysisResult."
            ) from exc
