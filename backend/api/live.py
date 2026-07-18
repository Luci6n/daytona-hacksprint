import asyncio
from collections.abc import Callable
from contextlib import suppress
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from backend.domain.live import LiveSessionState
from backend.domain.ports import AnalysisAgent, SpeechSynthesizer
from backend.models import (
    LiveFrameEvent,
    LiveInterruptEvent,
    LiveUtteranceEvent,
    live_client_event_adapter,
)
from backend.provider_errors import ProviderError


AgentFactory = Callable[[], AnalysisAgent]
SpeechFactory = Callable[[], SpeechSynthesizer]


def create_live_router(
    agent_factory: AgentFactory,
    speech_factory: SpeechFactory,
) -> APIRouter:
    router = APIRouter()

    @router.websocket("/live/{session_id}")
    async def live_session(websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        state = LiveSessionState(session_id=session_id)
        send_lock = asyncio.Lock()
        active_task: asyncio.Task[None] | None = None
        active_turn_id: str | None = None

        async def send_json(message: dict[str, object]) -> None:
            async with send_lock:
                await websocket.send_json(message)

        try:
            agent = agent_factory()
            speech = speech_factory()
        except (ProviderError, ValueError) as exc:
            await send_json(
                {
                    "type": "error",
                    "code": "configuration_error",
                    "detail": str(exc),
                }
            )
            await websocket.close(code=1011)
            return

        async def run_turn(turn_id: str, utterance: str) -> None:
            await send_json(
                {"type": "status", "state": "analyzing", "turnId": turn_id}
            )
            try:
                request = state.analysis_request(utterance)
                result = await asyncio.to_thread(
                    agent.analyze,
                    request,
                    state.conversation_context(),
                )
                state.previous_analysis = result
                await send_json(
                    {
                        "type": "analysis",
                        "turnId": turn_id,
                        "data": result.model_dump(by_alias=True, mode="json"),
                    }
                )
                await send_json(
                    {"type": "status", "state": "synthesizing", "turnId": turn_id}
                )
                if result.repair_steps:
                    first_step = result.repair_steps[0]
                    speech_text = (
                        f"{first_step.instruction} Safety: {first_step.safety_note}"
                    )
                else:
                    speech_text = f"I found {result.detected_item}."
                audio = await asyncio.to_thread(speech.synthesize, speech_text)
                async with send_lock:
                    await websocket.send_json(
                        {
                            "type": "audio",
                            "turnId": turn_id,
                            "contentType": "audio/wav",
                            "byteLength": len(audio),
                        }
                    )
                    await websocket.send_bytes(audio)
            except asyncio.CancelledError:
                raise
            except (ProviderError, ValueError) as exc:
                with suppress(WebSocketDisconnect, RuntimeError):
                    await send_json(
                        {
                            "type": "error",
                            "turnId": turn_id,
                            "code": "turn_failed",
                            "detail": str(exc),
                        }
                    )
            except Exception:
                with suppress(WebSocketDisconnect, RuntimeError):
                    await send_json(
                        {
                            "type": "error",
                            "turnId": turn_id,
                            "code": "internal_error",
                            "detail": "DaddyFix could not complete this turn.",
                        }
                    )

        await send_json({"type": "ready", "sessionId": session_id})
        try:
            while True:
                raw_event = await websocket.receive_json()
                try:
                    event = live_client_event_adapter.validate_python(raw_event)
                except ValidationError as exc:
                    await send_json(
                        {
                            "type": "error",
                            "code": "invalid_event",
                            "detail": str(exc),
                        }
                    )
                    continue

                if isinstance(event, LiveFrameEvent):
                    state.accept_frame(event.image_base64, event.device_hint)
                    await send_json({"type": "frameAccepted"})
                    continue

                if isinstance(event, LiveInterruptEvent):
                    is_active_turn = (
                        active_task is not None
                        and not active_task.done()
                        and event.turn_id == active_turn_id
                    )
                    if not is_active_turn:
                        await send_json(
                            {
                                "type": "error",
                                "code": "turn_mismatch",
                                "detail": "The requested turn is not active.",
                            }
                        )
                        continue
                    assert active_task is not None
                    active_task.cancel()
                    await send_json(
                        {"type": "interrupted", "turnId": event.turn_id}
                    )
                    continue

                if isinstance(event, LiveUtteranceEvent):
                    if active_task is not None and not active_task.done():
                        active_task.cancel()
                    active_turn_id = uuid4().hex
                    active_task = asyncio.create_task(
                        run_turn(active_turn_id, event.text)
                    )
        except WebSocketDisconnect:
            pass
        finally:
            if active_task is not None:
                if not active_task.done():
                    active_task.cancel()
                with suppress(asyncio.CancelledError, WebSocketDisconnect, RuntimeError):
                    await active_task

    return router
