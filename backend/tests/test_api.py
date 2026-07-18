from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.config import Settings


class FakeSpeechSynthesizer:
    def synthesize(self, text: str) -> bytes:
        assert text == 'Easy, sweetheart. Turn off the breaker first.'
        return b'RIFF-daddyfix-test-audio'


client = TestClient(
    create_app(
        Settings(demo_mode=True),
        speech_factory=FakeSpeechSynthesizer,
    )
)


def test_health_exposes_service_readiness_without_secrets() -> None:
    response = client.get('/health')

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert payload['service'] == 'daddyfix-backend'
    assert set(payload['providers']) == {
        'daytona',
        'kimi',
        'nosana',
        'nosanaTts',
        'oxylabs',
        'doubleword',
        'aiand',
    }
    assert 'apiKey' not in response.text
    assert 'password' not in response.text.lower()


def test_analyze_returns_water_heater_contract_in_demo_mode() -> None:
    response = client.post('/analyze', json={'symptom': 'No hot water'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['detectedItem'] == 'Rinnai Tankless Water Heater'
    assert payload['confidence'] == 0.94
    assert payload['arAnnotations'][0] == {
        'type': 'highlight',
        'x': 0.42,
        'y': 0.58,
        'z': None,
        'width': 0.18,
        'height': 0.12,
        'label': 'ELCB',
        'color': '#22C55E',
    }
    assert payload['repairSteps'][0]['safetyNote'] == (
        'If you smell gas or see scorch marks, stop and call a licensed professional.'
    )
    assert payload['buyableParts'][0]['x402Ready'] is True


def test_synthesize_returns_wav_audio() -> None:
    response = client.post(
        '/speech/synthesize',
        json={'text': 'Easy, sweetheart. Turn off the breaker first.'},
    )

    assert response.status_code == 200
    assert response.headers['content-type'] == 'audio/wav'
    assert response.content == b'RIFF-daddyfix-test-audio'


def test_openapi_exposes_ios_client_contract() -> None:
    response = client.get('/openapi.json')

    assert response.status_code == 200
    paths = response.json()['paths']
    assert {'/health', '/analyze', '/speech/synthesize'} <= set(paths)


def test_empty_speech_text_is_rejected_before_provider_call() -> None:
    response = client.post('/speech/synthesize', json={'text': ''})

    assert response.status_code == 422
