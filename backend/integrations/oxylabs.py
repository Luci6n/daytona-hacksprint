import json

import httpx

from backend.config import Settings
from backend.provider_errors import ProviderConfigurationError, ProviderResponseError


class OxylabsClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def search_repair_context(
        self,
        device_hint: str,
        symptom: str | None,
    ) -> str:
        if not self._settings.oxylabs_username or not self._settings.oxylabs_password:
            raise ProviderConfigurationError(
                "Oxylabs requires OXYLABS_USERNAME and OXYLABS_PASSWORD."
            )
        query = (
            f"{device_hint} {symptom or ''} manual troubleshooting replacement parts"
        ).strip()
        payload = {
            "source": "google_search",
            "query": query,
            "parse": True,
            "context": [{"key": "results_language", "value": "en"}],
        }
        try:
            response = httpx.post(
                self._settings.oxylabs_realtime_url,
                auth=(
                    self._settings.oxylabs_username,
                    self._settings.oxylabs_password,
                ),
                json=payload,
                timeout=45,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            # Do not hard-fail the whole /analyze path if scrape is unreachable
            # from the sandbox (common on restricted networks). Vision+reasoning
            # can still run with an empty product-context string.
            return (
                f'{{"oxylabsError": "{type(exc).__name__}", '
                f'"query": {json.dumps(query)}, '
                f'"note": "Product scrape unavailable; continue with vision/reasoning."}}'
            )

        return json.dumps(data, ensure_ascii=False)[:12_000]
