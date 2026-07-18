from openai import OpenAI

from backend.config import Settings
from backend.domain.ports import SafetyVerdict
from backend.models import AnalysisResult, AnalyzeRequest, VisionObservation
from backend.provider_errors import ProviderConfigurationError, ProviderResponseError


VISION_PROMPT = """Inspect this home-repair image and return JSON only.
Identify the device and visible issues. Produce normalized 0-to-1 image
coordinates for useful AR highlights, arrows, and labels. Do not provide repair
instructions; report only observations. Never claim to see a part that is not
visible. The JSON must match the supplied schema exactly.
"""


class DoublewordVisionClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.doubleword_api_key:
            raise ProviderConfigurationError(
                "Doubleword vision requires DOUBLEWORD_API_KEY."
            )
        self._settings = settings
        self._client = OpenAI(
            api_key=settings.doubleword_api_key,
            base_url=settings.doubleword_base_url,
        )

    def inspect(self, request: AnalyzeRequest) -> VisionObservation:
        if not request.image_base64:
            raise ValueError("imageBase64 is required when DEMO_MODE=false.")

        image_url = request.image_base64
        if not image_url.startswith("data:"):
            image_url = f"data:image/jpeg;base64,{image_url}"
        schema = VisionObservation.model_json_schema(by_alias=True)
        text = (
            f"{VISION_PROMPT}\n"
            f"Device hint: {request.device_hint or 'unknown'}\n"
            f"Reported symptom: {request.symptom or 'not provided'}\n"
            f"Required JSON schema: {schema}"
        )
        try:
            response = self._client.chat.completions.create(
                model=self._settings.doubleword_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": text},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
        except Exception as exc:
            raise ProviderResponseError(
                f"Doubleword vision request failed: {exc}"
            ) from exc

        content = response.choices[0].message.content
        if not content:
            raise ProviderResponseError("Doubleword vision returned an empty response.")
        try:
            return VisionObservation.model_validate_json(content)
        except ValueError as exc:
            raise ProviderResponseError(
                "Doubleword vision returned invalid observation JSON."
            ) from exc


class DoublewordSafetyClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.doubleword_api_key:
            raise ProviderConfigurationError(
                "Doubleword safety validation requires DOUBLEWORD_API_KEY."
            )
        self._settings = settings
        self._client = OpenAI(
            api_key=settings.doubleword_api_key,
            base_url=settings.doubleword_base_url,
        )

    def validate(self, result: AnalysisResult) -> SafetyVerdict:
        prompt = (
            "Audit this home-repair guidance. Reject instructions involving gas work, "
            "live electrical work, bypassed safety devices, missing safety notes, or "
            "unjustified certainty. Return JSON with approved:boolean and concerns:string[].\n"
            f"Guidance: {result.model_dump_json(by_alias=True)}"
        )
        try:
            response = self._client.chat.completions.create(
                model=self._settings.doubleword_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0,
            )
        except Exception as exc:
            raise ProviderResponseError(f"Doubleword request failed: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise ProviderResponseError("Doubleword returned an empty response.")
        try:
            return SafetyVerdict.model_validate_json(content)
        except ValueError as exc:
            raise ProviderResponseError(
                "Doubleword returned an invalid safety verdict."
            ) from exc
