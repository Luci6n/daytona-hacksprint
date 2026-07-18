import json
from urllib.parse import quote, quote_plus

import httpx

from backend.config import Settings
from backend.provider_errors import ProviderConfigurationError, ProviderResponseError


_MAX_CONTEXT_LENGTH = 12_000
_MAX_SEARCH_RESULTS = 10


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
        if self._settings.oxylabs_mode == "residential_proxy":
            return self._search_through_proxy(query)

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
            return (
                '{"oxylabsError": "%s", "query": %s, '
                '"note": "Product scrape unavailable; continue with vision/reasoning."}'
                % (type(exc).__name__, json.dumps(query))
            )

        try:
            return self._compact_web_scraper_context(data)
        except ProviderResponseError as exc:
            return (
                '{"oxylabsError": "%s", "note": "compact failed; continue without scrape."}'
                % (type(exc).__name__,)
            )

    def _compact_web_scraper_context(self, data: object) -> str:
        if not isinstance(data, dict):
            raise ProviderResponseError(
                "Oxylabs Web Scraper API returned an unexpected response."
            )

        raw_results = data.get("results")
        if not isinstance(raw_results, list) or not raw_results:
            raise ProviderResponseError(
                "Oxylabs Web Scraper API returned no search results."
            )

        first_result = raw_results[0]
        if not isinstance(first_result, dict):
            raise ProviderResponseError(
                "Oxylabs Web Scraper API returned an unexpected result."
            )
        content = first_result.get("content")
        if not isinstance(content, dict):
            raise ProviderResponseError(
                "Oxylabs Web Scraper API returned no parsed search content."
            )

        compact: dict[str, object] = {
            "source": "oxylabs_web_scraper_api",
            "searchUrl": self._bounded_text(content.get("url"), 2_000),
            "searchResults": [],
        }
        search_results = compact["searchResults"]
        if not isinstance(search_results, list):
            raise AssertionError("searchResults must be a list")

        parsed_results = content.get("results")
        if isinstance(parsed_results, dict):
            for result_type in ("organic", "featured_snippet", "paid"):
                items = parsed_results.get(result_type)
                if not isinstance(items, list):
                    continue
                for item in items:
                    normalized = self._normalize_search_result(item, result_type)
                    if normalized is None:
                        continue
                    candidate = {**compact, "searchResults": [*search_results, normalized]}
                    serialized = json.dumps(candidate, ensure_ascii=False)
                    if len(serialized) > _MAX_CONTEXT_LENGTH:
                        break
                    search_results.append(normalized)
                    if len(search_results) >= _MAX_SEARCH_RESULTS:
                        break
                if len(search_results) >= _MAX_SEARCH_RESULTS:
                    break

        return json.dumps(compact, ensure_ascii=False)

    def _normalize_search_result(
        self,
        item: object,
        result_type: str,
    ) -> dict[str, object] | None:
        if not isinstance(item, dict):
            return None
        title = self._bounded_text(item.get("title"), 500)
        url = self._bounded_text(item.get("url"), 2_000)
        description = self._bounded_text(
            item.get("desc") or item.get("description") or item.get("snippet"),
            1_500,
        )
        if not any((title, url, description)):
            return None
        return {
            "type": result_type,
            "position": item.get("pos") or item.get("position"),
            "title": title,
            "url": url,
            "description": description,
        }

    @staticmethod
    def _bounded_text(value: object, limit: int) -> str:
        return value[:limit] if isinstance(value, str) else ""

    def _search_through_proxy(self, query: str) -> str:
        username = self._settings.oxylabs_username or ""
        if not username.startswith("customer-"):
            username = f"customer-{username}"
        if "-cc-" not in username and self._settings.oxylabs_proxy_country:
            username = f"{username}-cc-{self._settings.oxylabs_proxy_country}"
        password = self._settings.oxylabs_password or ""
        proxy_origin = self._settings.oxylabs_proxy_url.removeprefix("http://")
        proxy_origin = proxy_origin.removeprefix("https://")
        proxy = (
            f"http://{quote(username, safe='')}:{quote(password, safe='')}@"
            f"{proxy_origin}"
        )
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        try:
            response = httpx.get(
                url,
                proxy=proxy,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
                        "AppleWebKit/605.1.15 Mobile/15E148"
                    )
                },
                timeout=45,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderResponseError(
                f"Oxylabs residential proxy request failed: {exc}"
            ) from exc
        if not response.text.strip():
            raise ProviderResponseError(
                "Oxylabs residential proxy returned empty search context."
            )
        return response.text[:12_000]
