# Kenji — Work Assignments (NO Xcode)

**Updated**: Kenji **cannot run Xcode**. All iOS/Swift/UI implementation is **Brian’s** until further notice.  
**Kenji** helps on **agent deployment / ops / docs / testing** that **does not collide with Lucian’s backend ownership**.

| Person | Now owns |
|--------|----------|
| **Brian** | **All Xcode**: AR + VisionService + VoiceManager + SwiftUI + payments + device QA |
| **Lucian** | Backend code, providers, architecture, `feature/lucian-backend` |
| **Kenji** | Deployment assist, sponsor ops, API smoke tests, docs, demo script — **no Swift** |

---

## What Kenji does **not** do

- ❌ Any Xcode / `.swift` files  
- ❌ VisionService / VoiceManager / ContentView / AppState implementation  
- ❌ Editing Lucian’s core agent pipeline without his OK (`daddy_agent`, providers, architecture refactors)  
- ❌ Putting secrets in git or iOS  

---

## What Kenji **can** do (no collision with Lucian)

Stay in **ops / verification / handoff** lane. Prefer **new docs, scripts, checklists, smoke tests** under `docs/` or root — not rewriting Lucian’s domain code.

### K-OPS-1 — Daytona persistent deploy (with Lucian’s OK) **P0**
- Follow `docs/deployment.md` (on Lucian’s branch when available)
- Create/run **persistent** sandbox that serves the API
- Produce **public HTTPS base URL** for Brian’s `APIConfig.baseURL`
- Document: start command, health URL, how to restart
- **Coordinate** with Lucian before changing his deploy process

**Done when:** Brian can hit `GET {url}/health` from phone/Mac and paste URL in team chat.

### K-OPS-2 — Env & readiness checklist (no secret values in git) **P0**
- Maintain a **checklist** of required env vars (names only): Moonshot/ai&, Doubleword, Oxylabs, Nosana TTS URL, etc.
- Verify `/health` flags match “ready” without printing secrets
- `.env.example` completeness only — **Lucian owns real keys**

### K-OPS-3 — API smoke tests (black-box) **P0**
Against Lucian’s running API (local or Daytona):

```text
GET  /health
POST /analyze   with small test JPEG + symptom + deviceHint
POST /speech/synthesize  with short text → save WAV, confirm playable
```

- Write results in `docs/smoke-test-log.md` (pass/fail, latency, errors — no keys)
- File bugs to Lucian with request/response shapes only

### K-OPS-4 — Nosana TTS deploy assist **P1**
Lucian’s progress: image/job not fully deployed.

Kenji can (if Lucian agrees):
- Help **Docker build/push** of `luci6n/daddyfix-qwen3-tts` if docs say so
- Help **market deploy / warmup** steps from `docs/`
- Run **real WAV** smoke after URL exists
- **Do not** redesign the TTS service code without Lucian

### K-OPS-5 — Sponsor / demo docs for judges **P0**
- One-pager: which sponsors used (Daytona, ai&/Kimi, Doubleword, Oxylabs, Nosana) and what each does in the demo
- Align with Lucian’s `docs/sponsor-integrations.md` — summarize, don’t contradict
- Judge talking points (30s stack story)

### K-OPS-6 — Demo script (product, not code) **P0**
- Write spoken demo script: heater one-shot + “live later”
- Safety lines (“call a pro”)
- Handoff moments: “Brian shows LiDAR lock… agent voice…”

### K-OPS-7 — Live WS prep (docs/tests only) **P1**
- Read Lucian’s live-session research / failing tests description
- Help write **client sequence docs** for Brian (1 fps JPEG, interrupt event)
- **Do not** implement the WebSocket route (that’s Lucian)

### K-OPS-8 — Contract guardian **P0**
- Keep a short **Python ↔ Swift field list** in sync in docs when Lucian changes OpenAPI
- Ping Brian if `AnalysisResult` fields change (`sessionId`, speech text fields, etc.)

---

## Explicit boundary with Lucian

| Lucian | Kenji |
|--------|--------|
| Agent code, providers, architecture | Run deploy steps Lucian documented |
| Implement `WS /live/...` | Document how Brian will call it later |
| Fix pytest / mypy in backend | Run pytest and report results |
| API design | Smoke test API as a consumer |
| Secrets in sandbox | Checklist that secrets are set (yes/no) |

**Rule:** If it changes Python under `backend/` domain logic → **Lucian**.  
If it is “run the thing, paste the URL, log the smoke test” → **Kenji**.

---

## Brian takes all former Kenji Xcode work

See **`BRIAN_IOS_TAKEOVER.md`**.

---

## Paste to Kenji

```text
@Kenji — no Xcode. All Swift/UI/voice code is Brian now.

You help deployment/ops without colliding with Lucian:
1. Daytona persistent public URL (with Lucian) → paste for Brian
2. Env readiness checklist (names only) + /health green
3. Black-box smoke: /health, /analyze, /speech/synthesize → log results
4. Nosana TTS deploy assist if Lucian wants hands
5. Judge one-pager (sponsors) + demo script
6. Watch AnalysisResult contract; ping Brian on changes
7. Live WS: docs only until Lucian implements

Do not rewrite Lucian’s agent/providers. Do not commit secrets.
Details: KENJI_ASSIGNMENTS.md
```
