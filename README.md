# DaddyFix — Daytona Hacksprint

Spatial AR home repair on **iPhone 17 Pro LiDAR** + cloud **Daddy Agent** on **Daytona** (Kimi / Doubleword / Oxylabs / Nosana).

## Docs

| Doc | Purpose |
|-----|---------|
| [`PRD.md`](./PRD.md) | Product + status board |
| [`AGENTS.md`](./AGENTS.md) | Roles / ownership |
| [`docs/README.md`](./docs/README.md) | **Lucian backend** API, architecture, deploy, sponsors |
| [`docs/backend-api.md`](./docs/backend-api.md) | Paste-ready HTTP + live WS contract |
| [`docs/CONTINUOUS_ANALYSIS.md`](./docs/CONTINUOUS_ANALYSIS.md) | 1–2s continuous frames / RTSP decision |
| [`docs/MERGE_BACKEND.md`](./docs/MERGE_BACKEND.md) | What we kept vs discarded in backend merge |
| [`BRIAN_IOS_TAKEOVER.md`](./BRIAN_IOS_TAKEOVER.md) | All Xcode → Brian |
| [`KENJI_ASSIGNMENTS.md`](./KENJI_ASSIGNMENTS.md) | Kenji ops (no Xcode) |
| [`DaddyFix/BRIAN_SETUP.md`](./DaddyFix/BRIAN_SETUP.md) | On-device AR setup |

## Backend (Lucian’s tree — source of truth)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

```bash
# macOS / zsh
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements-dev.txt
uvicorn backend.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/docs`.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Readiness (no secrets) |
| POST | `/analyze` | `symptom`, `deviceHint`, `imageBase64` → `AnalysisResult` |
| POST | `/speech/synthesize` | text → WAV |
| WS | `/live/{sessionId}` | Continuous live session (see Lucian docs) |

## Architecture (one line)

Phone sends **frames/events** (~1–2s) → **Daytona agent** reasons → phone **LiDAR-locks** annotations. Keys stay in the cloud.

## Team (current)

| Person | Focus |
|--------|--------|
| **Brian** | **All Xcode / iOS** (AR + clients + UI + device) |
| **Lucian** | **All backend** (`backend/`, providers, live WS) |
| **Kenji** | Deploy/smoke/docs — **no Xcode**, don’t rewrite Lucian’s agent |

## iOS

```bash
open DaddyFix/DaddyFix.xcodeproj
```

Real **LiDAR iPhone** required for the hero demo.
