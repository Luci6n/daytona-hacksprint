import httpx
import pytest

from backend.config import Settings
from backend.integrations.nosana import NosanaSpeechClient
from backend.integrations.oxylabs import OxylabsClient
from backend.provider_errors import ProviderResponseError


class StubResponse:
    def __init__(
        self,
        *,
        content: bytes = b'',
        text: str = '',
        content_type: str = 'application/octet-stream',
    ) -> None:
        self.content = content
        self.text = text
        self.headers = {'content-type': content_type}

    def raise_for_status(self) -> None:
        return None


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
