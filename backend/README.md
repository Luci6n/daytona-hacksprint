# DaddyFix backend

FastAPI backend for the DaddyFix iOS LiDAR app. It exposes the shared
`AnalysisResult` JSON contract and orchestrates sponsor integrations.

See [`../docs/backend-api.md`](../docs/backend-api.md) for the complete
`VisionService.swift` integration contract, REST/WebSocket examples, error
handling, and voice flow.

## Architecture

```text
backend/main.py                 Stable ASGI entrypoint
backend/api/                    FastAPI app, routes, and HTTP error mapping
backend/domain/                 Provider-independent Daddy Agent and ports
backend/integrations/           Kimi, Doubleword, Oxylabs, and Nosana adapters
backend/models.py               Shared Python-first AnalysisResult contract
backend/speech_service/         Qwen3-TTS GPU service deployable on Nosana
```

The application factory injects sponsor adapters into the domain agent. This
keeps demo mode deterministic and lets tests exercise the live orchestration
without making paid network calls.

## Credential setup

Use the repository-root `.env.local` for secrets. `.env` and `.env.local` are
ignored by Git; `.env.example` documents every supported setting.

Required for the live core flow:

- `MOONSHOT_API_KEY`, or all three ai& settings
  (`AIAND_API_KEY`, `AIAND_BASE_URL`, `AIAND_MODEL`)
- `OXYLABS_USERNAME`
- `OXYLABS_PASSWORD`

Optional integrations:

- `DOUBLEWORD_API_KEY` is required for visual observation on the ai& path and
  also enables the second-pass safety audit. It is optional on the direct
  Moonshot vision path.
- `NOSANA_API_KEY` enables GPU market/job operations.
- `NOSANA_TTS_URL` enables Qwen3-TTS audio through a Nosana GPU endpoint.
- `DAYTONA_API_KEY` enables sandbox orchestration.
- `OXYLABS_MODE=residential_proxy` uses the current proxy-user credentials.
  `web_scraper_api` is available when a separate Web Scraper API user exists.
- `OXYLABS_AI_STUDIO_API_KEY` is not used by either current path.

`DEMO_MODE=true` returns the deterministic Rinnai/ELCB fixture without spending
provider credits. Set it to `false` to require an image and call live providers.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation.

## API summary

The detailed client contract is in [`../docs/backend-api.md`](../docs/backend-api.md). FastAPI also exposes
interactive Swagger documentation at `http://127.0.0.1:8000/docs`.

### `GET /health`

Returns service status and boolean provider readiness. It never returns keys.

### `POST /analyze`

```json
{
  "symptom": "No hot water",
  "deviceHint": "Rinnai tankless water heater",
  "imageBase64": "data:image/jpeg;base64,..."
}
```

In live mode, the agent:

1. retrieves repair/manual context using Oxylabs;
2. localizes visible parts with Doubleword's Qwen3-VL model when using ai&;
3. asks Kimi through Moonshot or ai& to produce the repair guidance;
4. validates the structured result against the Swift contract;
5. optionally asks Doubleword to reject unsafe guidance.

Provider failures return explicit `502`/`503` responses; they do not silently
fall back to demo data when `DEMO_MODE=false`.

### `WS /live/{sessionId}`

Maintains the newest sampled camera frame and prior completed analysis for
Gemini-Live-style follow-up turns. The iOS app sends JPEG frame, utterance, and
interrupt events; the backend sends structured analysis followed by WAV audio.
See the complete event sequence and barge-in rules in
[`../docs/backend-api.md`](../docs/backend-api.md#ws-livesessionid).

### `POST /speech/synthesize`

Accepts `{"text": "Turn off the breaker first."}` and returns `audio/wav` from
the configured Qwen3-TTS VoiceDesign service. Apple Speech recognition remains
an iOS responsibility; the resulting transcript is sent to `/analyze` as the
`symptom` field.

The independently deployable GPU service lives in `backend/speech_service`.
Build and push its Docker image, deploy `nosana-job.example.json` on Nosana,
then copy the exposed URL
into `NOSANA_TTS_URL`. Call the service's `/warmup` route once before the demo so
the model weights are loaded.

## Daytona

Install the orchestration-only dependency and run the sandbox smoke check:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-daytona.txt
.\.venv\Scripts\python.exe -m backend.daytona_sandbox smoke
```

Deployment and cleanup commands are documented in
[`../docs/deployment.md`](../docs/deployment.md).

The production container entrypoint is defined in `backend/Dockerfile`.
