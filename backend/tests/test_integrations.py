import json
from types import SimpleNamespace

import httpx
import pytest

from backend.config import Settings
from backend.demo import water_heater_result
from backend.integrations.doubleword import (
    DoublewordSafetyClient,
    DoublewordVisionClient,
)
from backend.integrations.nosana import NosanaSpeechClient
from backend.integrations.oxylabs import OxylabsClient
from backend.models import AnalyzeRequest
from backend.provider_errors import ProviderResponseError


class StubResponse:
    def __init__(
        self,
        *,
        content: bytes = b'',
        text: str = '',
        content_type: str = 'application/octet-stream',
        json_data: object | None = None,
    ) -> None:
        self.content = content
        self.text = text
        self.headers = {'content-type': content_type}
        self._json_data = json_data

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._json_data


class StubCompletions:
    def __init__(self, content: str, captured: dict[str, object]) -> None:
        self._content = content
        self._captured = captured

    def create(self, **kwargs: object) -> object:
        self._captured.update(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(message=SimpleNamespace(content=self._content))
            ]
        )


def stub_openai_client(
    content: str,
    captured: dict[str, object],
) -> object:
    return SimpleNamespace(
        chat=SimpleNamespace(
            completions=StubCompletions(content, captured),
        )
    )


def test_doubleword_uses_strict_structured_outputs_for_both_calls() -> None:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        doubleword_api_key='inference-secret',
    )
    vision_args: dict[str, object] = {}
    vision = DoublewordVisionClient(settings)
    vision._client = stub_openai_client(  # type: ignore[assignment]
        json.dumps(
            {
                'detectedItem': 'Rinnai water heater',
                'confidence': 0.95,
                'visibleIssues': [],
                'arAnnotations': [],
            }
        ),
        vision_args,
    )
    vision.inspect(AnalyzeRequest(image_base64='encoded-frame'))

    safety_args: dict[str, object] = {}
    safety = DoublewordSafetyClient(settings)
    safety._client = stub_openai_client(  # type: ignore[assignment]
        '{"approved":true,"concerns":[]}',
        safety_args,
    )
    safety.validate(water_heater_result())

    for request_args, schema_name in (
        (vision_args, 'vision_observation'),
        (safety_args, 'safety_verdict'),
    ):
        response_format = request_args['response_format']
        assert isinstance(response_format, dict)
        assert response_format['type'] == 'json_schema'
        json_schema = response_format['json_schema']
        assert isinstance(json_schema, dict)
        assert json_schema['name'] == schema_name
        assert json_schema['strict'] is True
        assert isinstance(json_schema['schema'], dict)


def test_oxylabs_residential_proxy_collects_search_html(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_get(url: str, **kwargs: object) -> StubResponse:
        captured['url'] = url
        captured.update(kwargs)
        return StubResponse(text='<html>Rinnai manual result</html>')

    monkeypatch.setattr(httpx, 'get', fake_get)
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        oxylabs_mode='residential_proxy',
        oxylabs_username='proxy-user',
        oxylabs_password='proxy-password',
        oxylabs_proxy_country='US',
    )

    result = OxylabsClient(settings).search_repair_context(
        'Rinnai SENSEI RX',
        'no hot water',
    )

    assert result == '<html>Rinnai manual result</html>'
    assert str(captured['url']).startswith('https://www.google.com/search?')
    assert 'customer-proxy-user-cc-US' in str(captured['proxy'])


def test_oxylabs_web_scraper_returns_bounded_valid_search_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    oversized_page_data = 'irrelevant page data ' * 2_000

    def fake_post(*args: object, **kwargs: object) -> StubResponse:
        return StubResponse(
            json_data={
                'job': {'id': 'job-123'},
                'results': [
                    {
                        'content': {
                            'last_visible_page': 10,
                            'page': 1,
                            'parse_status_code': 12000,
                            'results': {
                                'organic': [
                                    {
                                        'pos': 1,
                                        'title': 'Rinnai SENSEI RX service manual',
                                        'url': 'https://example.test/rinnai-manual',
                                        'desc': 'Official troubleshooting and safety guidance.',
                                    }
                                ],
                                'page_data': oversized_page_data,
                            },
                            'url': 'https://www.google.com/search?q=rinnai',
                        },
                        'status_code': 200,
                    }
                ],
            }
        )

    monkeypatch.setattr(httpx, 'post', fake_post)
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        oxylabs_mode='web_scraper_api',
        oxylabs_username='scraper-user',
        oxylabs_password='scraper-password',
    )

    context = OxylabsClient(settings).search_repair_context(
        'Rinnai SENSEI RX',
        'no hot water',
    )

    parsed_context = json.loads(context)
    assert len(context) <= 12_000
    assert 'Rinnai SENSEI RX service manual' in context
    assert 'https://example.test/rinnai-manual' in context
    assert 'Official troubleshooting and safety guidance.' in context
    assert oversized_page_data not in context
    assert parsed_context['searchResults'][0]['position'] == 1


def test_nosana_speech_rejects_non_wav_response(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*args: object, **kwargs: object) -> StubResponse:
        return StubResponse(content=b'not-wave', content_type='text/plain')

    monkeypatch.setattr(httpx, 'post', fake_post)
    client = NosanaSpeechClient(
        Settings(  # type: ignore[call-arg]
            _env_file=None,
            nosana_tts_url='https://tts.example.test',
        )
    )

    with pytest.raises(ProviderResponseError, match='valid WAV'):
        client.synthesize('Safety first.')
