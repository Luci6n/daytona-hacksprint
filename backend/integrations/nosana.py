import httpx

from backend.config import Settings
from backend.provider_errors import ProviderConfigurationError, ProviderResponseError


class NosanaClient:
    """REST adapter for Nosana GPU market and deployment operations."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def list_markets(self) -> object:
        if not self._settings.nosana_api_key:
            raise ProviderConfigurationError("Nosana requires NOSANA_API_KEY.")
        try:
            response = httpx.get(
                f"{self._settings.nosana_base_url.rstrip('/')}/markets",
                headers={
                    "Authorization": f"Bearer {self._settings.nosana_api_key}",
                },
                timeout=20,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise ProviderResponseError(f"Nosana request failed: {exc}") from exc


class NosanaSpeechClient:
    """Proxy DaddyFix speech requests to a Qwen3-TTS service on Nosana."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def synthesize(self, text: str) -> bytes:
        endpoint = self._settings.nosana_tts_url
        if not endpoint:
            raise ProviderConfigurationError(
                "Speech synthesis requires NOSANA_TTS_URL."
            )

        headers: dict[str, str] = {}
        if self._settings.nosana_tts_bearer_token:
            headers["Authorization"] = (
                f"Bearer {self._settings.nosana_tts_bearer_token}"
            )
        try:
            response = httpx.post(
                f"{endpoint.rstrip('/')}/synthesize",
                headers=headers,
                json={
                    "text": text,
                    "language": self._settings.tts_language,
                    "instruct": self._settings.tts_voice_description,
                },
                timeout=self._settings.tts_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderResponseError(
                f"Nosana TTS request failed: {exc}"
            ) from exc

        content_type = response.headers.get("content-type", "").lower()
        is_wav = (
            len(response.content) >= 12
            and response.content[:4] == b"RIFF"
            and response.content[8:12] == b"WAVE"
        )
        if "audio/wav" not in content_type or not is_wav:
            raise ProviderResponseError("Nosana TTS did not return valid WAV audio.")
        return response.content
