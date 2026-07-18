# DaddyFix backend architecture

## Goals

The backend must keep the water-heater demo deterministic, expose a stable
Swift-compatible JSON contract, and use sponsor services without coupling the
core repair workflow to any one SDK.

```text
iOS / VisionService
        |
        v
FastAPI routes and error mapping        backend/api/
        |
        v
DaddyAgent orchestration + ports        backend/domain/
        |
        +--> Oxylabs manual context
        +--> Doubleword visual observation
        +--> Moonshot Kimi or ai& Qwen reasoning
        +--> Doubleword safety validation

iOS / VoiceManager
        |
        v
POST /speech/synthesize
        |
        +--> Nosana-hosted Qwen3-TTS GPU service

iOS live camera session
        |
        v
WS /live/{sessionId}                    backend/api/live.py
        |
        +--> connection-local latest frame + prior analysis
        +--> DaddyAgent analysis task
        +--> AnalysisResult event
        +--> Nosana WAV metadata + binary audio
```

## Layer boundaries

### Stable entrypoints

- `backend/main.py` exposes the ASGI `app` used by Uvicorn and Daytona.
- `backend/models.py` is the Python-first shared wire contract.
- `backend/daddy_agent.py` re-exports the agent for team-facing compatibility.

### HTTP layer — `backend/api/`

- Builds the FastAPI application.
- Defines `/health`, `/analyze`, `/speech/synthesize`, and the `/live/{sessionId}`
  WebSocket.
- Converts domain/provider exceptions into the documented HTTP error contract.
- Does not contain sponsor SDK logic.

### Domain layer — `backend/domain/`

- `DaddyAgent` owns provider ordering and safety rejection behavior.
- `ports.py` defines structural protocols for repair context, vision, reasoning,
  safety, and speech.
- The domain does not import FastAPI, HTTPX, OpenAI, or Daytona.

### Integration layer — `backend/integrations/`

- `oxylabs.py`: manual/product search context.
- `doubleword.py`: Qwen3-VL visual observation and safety audit.
- `kimi.py`: Moonshot/ai& OpenAI-compatible reasoning.
- `nosana.py`: Nosana control-plane calls and Qwen3-TTS endpoint proxy.

### Composition root — `backend/bootstrap.py`

The bootstrap module is the only place that decides which concrete providers
implement the domain ports. Demo mode creates an agent with no paid providers.
Live mode builds providers from `Settings` at request time, so a missing
credential returns a clear `503` rather than preventing the API from starting.

## `/analyze` sequence

### Demo mode

1. Receive any valid `AnalyzeRequest`.
2. Return the deterministic Rinnai/ELCB fixture.
3. Make zero sponsor network calls.

### Moonshot live mode

1. Oxylabs retrieves repair/manual context.
2. Kimi K2.6 receives that context plus the image.
3. The response is validated against `AnalysisResult`.
4. If Doubleword is configured, it audits the final safety guidance.

### ai& live mode

1. Oxylabs retrieves repair/manual context.
2. Doubleword Qwen3-VL turns the image into a structured visual observation.
3. ai&-hosted Qwen3.6 27B reasons over the observation and context.
4. The response is validated against `AnalysisResult`.
5. Doubleword audits the final safety guidance.

Live provider failures never silently return the demo fixture.

Oxylabs supports two explicit credential products. The current hackathon
profile uses `residential_proxy` mode to retrieve search pages through
`pr.oxylabs.io`; `web_scraper_api` mode uses the structured Realtime API only
when a separate Web Scraper API user is configured.

## Dependency injection and testing

`create_app()` accepts agent and speech factories. `DaddyAgent` accepts provider
ports through `AgentProviders`. Tests therefore verify paid-provider sequencing
with in-memory fakes and can test WAV responses without calling Nosana.

Current contract tests cover:

- health output without secrets;
- the exact water-heater JSON response;
- the live provider sequence;
- demo operation without provider dependencies;
- TTS WAV behavior and text validation;
- OpenAPI route exposure;
- Daytona environment filtering and CLI defaults.
- live frame state, follow-up context, WAV delivery, and interruption acknowledgement.

## Live-session sequence and limitations

`backend/api/live.py` keeps one `LiveSessionState` per WebSocket connection. A
frame event replaces the cached image. An utterance starts an asyncio task that
runs the synchronous agent and speech adapters in worker threads, allowing the
receive loop to process an interrupt while analysis is in progress.

Cancelling that asyncio task prevents old analysis/audio from being delivered,
but Python cannot terminate a synchronous provider request already running in
`asyncio.to_thread`. The iOS client therefore stops audio locally and rejects
late events by `turnId`. The current TTS handoff sends a complete WAV rather
than streaming chunks, and live state does not survive reconnects or multiple
backend replicas.

## Extension rules

1. Add or change wire fields in `backend/models.py` first.
2. Agree on matching changes to `AnalysisResult.swift` before editing Swift.
3. Add a domain port when the agent needs a new capability.
4. Implement sponsor-specific behavior only in `backend/integrations/`.
5. Wire the adapter in `backend/bootstrap.py`.
6. Add orchestration and HTTP contract tests before changing public behavior.
7. Never catch a provider error and return fake live guidance.
