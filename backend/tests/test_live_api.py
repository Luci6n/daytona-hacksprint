import time

from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.config import Settings
from backend.demo import water_heater_result
from backend.models import AnalysisResult, AnalyzeRequest


class LiveAgent:
    def __init__(self) -> None:
        self.contexts: list[str | None] = []

    def analyze(
        self,
        request: AnalyzeRequest,
        conversation_context: str | None = None,
    ) -> AnalysisResult:
        assert request.image_base64 == 'data:image/jpeg;base64,frame-one'
        self.contexts.append(conversation_context)
        return water_heater_result()


class LiveSpeech:
    def synthesize(self, text: str) -> bytes:
        assert 'Earth Leakage Circuit Breaker' in text
        return b'RIFF-live-daddy-audio'


def test_live_session_uses_latest_frame_and_preserves_turn_context() -> None:
    agent = LiveAgent()
    client = TestClient(
        create_app(
            Settings(demo_mode=True),
            agent_factory=lambda: agent,  # type: ignore[arg-type]
            speech_factory=LiveSpeech,
        )
    )

    with client.websocket_connect('/live/kitchen-demo') as socket:
        assert socket.receive_json() == {
            'type': 'ready',
            'sessionId': 'kitchen-demo',
        }
        socket.send_json(
            {
                'type': 'frame',
                'imageBase64': 'data:image/jpeg;base64,frame-one',
                'deviceHint': 'Rinnai tankless water heater',
            }
        )
        assert socket.receive_json()['type'] == 'frameAccepted'

        socket.send_json({'type': 'utterance', 'text': 'What should I check?'})
        status = socket.receive_json()
        assert status['type'] == 'status'
        assert status['state'] == 'analyzing'
        first_analysis = socket.receive_json()
        assert first_analysis['type'] == 'analysis'
        assert first_analysis['data']['detectedItem'] == 'Rinnai Tankless Water Heater'
        assert socket.receive_json()['state'] == 'synthesizing'
        assert socket.receive_json()['type'] == 'audio'
        assert socket.receive_bytes() == b'RIFF-live-daddy-audio'

        socket.send_json({'type': 'utterance', 'text': 'What about that switch?'})
        assert socket.receive_json()['state'] == 'analyzing'
        assert socket.receive_json()['type'] == 'analysis'
        assert socket.receive_json()['state'] == 'synthesizing'
        assert socket.receive_json()['type'] == 'audio'
        socket.receive_bytes()

    assert agent.contexts[0] is None
    assert agent.contexts[1] is not None
    assert 'Rinnai Tankless Water Heater' in agent.contexts[1]


def test_live_session_acknowledges_barge_in_during_analysis() -> None:
    class SlowAgent:
        def analyze(
            self,
            request: AnalyzeRequest,
            conversation_context: str | None = None,
        ) -> AnalysisResult:
            time.sleep(0.5)
            return water_heater_result()

    client = TestClient(
        create_app(
            Settings(demo_mode=True),
            agent_factory=SlowAgent,  # type: ignore[arg-type]
            speech_factory=LiveSpeech,
        )
    )

    with client.websocket_connect('/live/interruption-demo') as socket:
        socket.receive_json()
        socket.send_json(
            {
                'type': 'frame',
                'imageBase64': 'data:image/jpeg;base64,frame-one',
            }
        )
        socket.receive_json()
        socket.send_json({'type': 'utterance', 'text': 'Start explaining.'})
        status = socket.receive_json()
        assert status['state'] == 'analyzing'
        socket.send_json({'type': 'interrupt', 'turnId': status['turnId']})

        interrupted = socket.receive_json()
        assert interrupted == {
            'type': 'interrupted',
            'turnId': status['turnId'],
        }
