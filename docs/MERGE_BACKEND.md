# Backend merge analysis — Lucian wins

**Date**: merge of `origin/feature/lucian-backend` into `main`  
**Policy**: On backend conflict → **keep Lucian**. Keep **main** iOS / role docs.

---

## What we **kept** (Lucian)

| Path | Why |
|------|-----|
| `backend/api/` | FastAPI app, routes, **live WS**, errors |
| `backend/domain/` | Agent + live domain + ports |
| `backend/integrations/` | Doubleword, Kimi, Oxylabs, Nosana |
| `backend/speech_service/` | Nosana Qwen3-TTS Docker/job |
| `backend/config.py`, `bootstrap.py`, `demo.py` | Settings + demo fixture |
| `backend/daytona_sandbox.py` | Daytona smoke helper |
| `backend/models.py` | `AnalyzeRequest` (`symptom`, `deviceHint`, `imageBase64`), camelCase aliases, live events |
| `backend/tests/` | API / agent / live / daytona tests |
| `backend/Dockerfile`, `requirements*.txt` | Deploy |
| `docs/backend-*.md`, `deployment.md`, `sponsor-*.md`, `team-handoff.md`, `live-camera-research.md` | Operator + client contract |
| Root `.env.example` | Lucian’s env template |

### Lucian API (use this)

- `GET /health`
- `POST /analyze` — body: `symptom`, `deviceHint`, `imageBase64`
- `POST /speech/synthesize` — text → `audio/wav`
- `WS /live/{sessionId}` — continuous frames / utterance / interrupt (see `docs/backend-api.md`)

### Continuous analysis (Lucian design)

- ~**1 FPS** JPEG over live session (not 30 FPS video)
- Not the discarded Brian RTSP loop — re-add RTSP **inside Lucian’s** architecture only if needed later

---

## What we **discarded** (Brian scaffold on main)

| Path | Why discard |
|------|-------------|
| `backend/main.py` (old monolith) | Replaced by Lucian `backend.main:app` package entry |
| `backend/vision.py` | Lucian integrations/* + domain agent |
| `backend/rtsp_ingest.py` | Not in Lucian tree; continuous = his WS/live |
| `backend/stream_session.py` | Replaced by `domain/live.py` + `api/live.py` |
| `backend/nosana_client.py` | Replaced by `integrations/nosana.py` + speech_service |
| `backend/oxylabs_client.py` | Replaced by `integrations/oxylabs.py` |
| `backend/.env.example` | Root `.env.example` is Lucian’s |

**Local `backend/.env`**: never committed; recreate from root `.env.example` if needed.

---

## What we **kept from main** (not Lucian’s older iOS)

| Path | Why |
|------|-----|
| `DaddyFix/**` current | AR, VisionService, UI (VoiceManager, Payment, RepairGuide), AppState — **ahead of Lucian’s branch** (his branch forked earlier) |
| `AGENTS.md`, `PRD.md`, role handoffs | Brian full iOS / Kenji ops split |
| `BRIAN_IOS_TAKEOVER.md`, `KENJI_ASSIGNMENTS.md`, `TEAM_CONTINUE.md` | Current team truth |
| `docs/CONTINUOUS_ANALYSIS.md` | Product decision 1–2s frames |

Lucian’s **old** `DaddyFix` snapshot on his branch was **not** used to overwrite iOS.

---

## iOS client alignment TODO (Brian)

Match Lucian’s contract in `VisionService`:

```json
POST /analyze
{
  "symptom": "...",
  "deviceHint": "Rinnai water heater",
  "imageBase64": "..."
}
```

- Decode camelCase `AnalysisResult` (already aligned field names)
- `POST /speech/synthesize` `{ "text": "..." }` → WAV
- Live: implement WS client per `docs/backend-api.md` when URL ready
- **No silent mock** on live server errors (Lucian policy)

Optional Swift fields `sessionId` / `seq` / `eventType` are extra; safe if Lucian doesn’t send them (need optional decoding — already optional).

---

## Run after merge

```bash
# From repo root
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements-dev.txt
uvicorn backend.main:app --reload --port 8000
# NOT: cd backend && uvicorn main:app  (unless path hacks — prefer package form)
```

```bash
pytest backend/tests -q
```

---

## Summary

| Layer | Winner |
|-------|--------|
| Cloud backend | **Lucian** |
| iOS / AR | **Main / Brian** |
| Deploy docs | **Lucian** |
| Team roles (no Xcode Kenji) | **Main docs** |
| Continuous 1–2s / live | **Lucian WS design** + Brian phone client |
