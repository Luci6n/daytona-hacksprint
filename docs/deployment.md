# Backend and speech deployment

## What runs where

- FastAPI/Daddy Agent: local Windows during development; Daytona for the public
  demo endpoint.
- Qwen3-TTS VoiceDesign: separate GPU container on Nosana.
- Apple Speech ASR: on the iPhone, not in either backend deployment.

## Local backend

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
Copy-Item .env.example .env.local
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

Do not overwrite an existing `.env.local` containing credentials. Verify:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Start-Process http://127.0.0.1:8000/docs
```

Use `DEMO_MODE=true` until the deterministic hero flow works end-to-end. Switch
to `false` only when testing live providers with an image.

## Minimal environment profiles

Teammates do not need every field from `.env.example`:

| Use case | Required configuration |
| --- | --- |
| Kenji/Brian call a deployed API | Backend base URL in the iOS app; no sponsor credentials. |
| Local deterministic demo | `DEMO_MODE=true`; no sponsor credentials. |
| Live analysis through ai& | `DEMO_MODE=false`, Oxylabs Web Scraper API username/password with `OXYLABS_MODE=web_scraper_api`, complete ai& key/base/model, and a Doubleword inference key for image observation. |
| Live analysis through Moonshot | `DEMO_MODE=false`, Oxylabs credentials/mode, and a Moonshot key. Doubleword is optional for the final safety audit. |
| Call deployed sugar-daddy TTS | `NOSANA_TTS_URL`; bearer token only if the deployed endpoint adds one. |
| Create/manage Nosana deployment | `NOSANA_API_KEY` on the operator's machine. |
| Create/manage Daytona sandbox | `DAYTONA_API_KEY` on the operator's machine. |

`OXYLABS_AI_STUDIO_API_KEY` is not used. Residential Proxy and Web Scraper API
are separate Oxylabs products with different credential types.
Keep `.env` and `.env.local` local; distribute access through sponsor team
dashboards or a secret manager rather than Git or chat.

## Backend checks

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m mypy backend --exclude backend/tests
```

## Daytona smoke check

Install the orchestration-only dependency:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-daytona.txt
```

The smoke command creates an ephemeral Python sandbox, executes
`python --version`, and deletes the sandbox in a `finally` block:

```powershell
.\.venv\Scripts\python.exe -m backend.daytona_sandbox smoke
```

This command creates an external resource briefly and requires Daytona credit.

## Deploy FastAPI to Daytona

The branch must be committed and pushed to a repository Daytona can clone.
For a private repository, configure repository access in Daytona first; the
helper does not accept a Git token on the command line.

```powershell
.\.venv\Scripts\python.exe -m backend.daytona_sandbox deploy `
  --repo-url https://github.com/OWNER/REPOSITORY.git `
  --branch feature/lucian-backend
```

The helper:

1. creates a private Python 3.12 sandbox with a six-hour TTL;
2. applies a least-privilege Daytona `domain_allow_list` for GitHub/PyPI setup
   plus the configured Oxylabs, Doubleword, ai&, and Nosana TTS hosts;
3. passes runtime provider configuration into the sandbox, but never the
   Daytona, Moonshot, or Nosana control-plane keys;
4. clones the selected branch and installs backend requirements;
5. starts Uvicorn on port 8000 in a persistent session;
6. prints the sandbox ID and a six-hour signed preview URL.

Daytona's outbound firewall can reset TLS before a request reaches a provider.
Do not treat that reset as an expired sponsor key. The deploy helper derives
hostnames from provider URLs and sends them as `domain_allow_list`; it never
copies URL credentials, paths, ports, or query strings into the rule. See
[`daytona-outbound-network.md`](daytona-outbound-network.md) for the reproduced
failure, official Daytona constraints, live-update command, and verification
checklist.

Verify `<PREVIEW_URL>/health` and `<PREVIEW_URL>/docs`. A signed preview URL
contains access material; share it only with the integration team.

For live-camera integration, convert the preview origin from `https://` to
`wss://` and append `/live/<session-id>`. Verify that the chosen preview/proxy
supports WebSocket upgrades before handing the URL to Kenji.

Delete the sandbox immediately after the demo:

```powershell
.\.venv\Scripts\python.exe -m backend.daytona_sandbox delete SANDBOX_ID
```

The sandbox also has an automatic lifetime, but explicit deletion avoids
unnecessary usage. Daytona preview links and signed preview URLs have different
authentication behavior; the helper uses a signed URL so the iOS app does not
need a preview-token header. See the
[Daytona preview documentation](https://www.daytona.io/docs/en/preview/).

## Build the Qwen3-TTS image

The Docker build context must be the repository root:

```powershell
docker build `
  -f backend/speech_service/Dockerfile `
  -t docker.io/luci6n/daddyfix-qwen3-tts:latest `
  .
docker push docker.io/luci6n/daddyfix-qwen3-tts:latest
```

The image uses CUDA, Python 3.12, and the official `qwen-tts` package. Model
weights download on the first start, so initial startup is slower.

## Deploy TTS to Nosana

1. Copy `backend/speech_service/nosana-job.example.json`.
2. Select a Nosana market with at least the requested 16 GB VRAM.
3. Create a deployment in the Nosana dashboard, or post the job definition with
   the Nosana CLI.
4. Copy the exposed service URL to `NOSANA_TTS_URL` in the backend environment.
5. Call `<NOSANA_TTS_URL>/warmup` before the demo.
6. Confirm `<NOSANA_TTS_URL>/health` reports `modelLoaded: true`.

Nosana exposes long-running container services through the `expose` field in a
job definition. See the
[Nosana service documentation](https://learn.nosana.com/deployments/jobs/job-definition/services.html).

The service endpoints are:

- `GET /health` — process/model status;
- `POST /warmup` — load Qwen3-TTS onto the GPU;
- `POST /synthesize` — internal JSON-to-WAV endpoint used by FastAPI.

## Deployment readiness checklist

- `/health` returns `status: ok`.
- `demoMode` matches the intended demo path.
- `POST /analyze` decodes into the checked-in Swift fixture.
- Nosana TTS has been warmed and `/speech/synthesize` returns `audio/wav`.
- The iPhone can reach the Daytona signed URL over its current network.
- The public proxy accepts a `wss://.../live/<session-id>` WebSocket upgrade.
- The Daytona sandbox ID and Nosana deployment ID are recorded for cleanup.
- No `.env`, `.env.local`, API key, or preview token is committed.
