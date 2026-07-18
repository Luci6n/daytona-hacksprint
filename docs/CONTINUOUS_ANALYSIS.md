# Continuous analysis (RTSP / 1–2s frames) — team decision

## Merge rule (backend)

When Lucian’s branch lands (`feature/lucian-backend` or equivalent):

| Keep | Discard / do not fight |
|------|-------------------------|
| **Lucian’s** `backend/` structure, providers, OpenAPI, WS live, TTS | **Brian’s earlier** scaffold (`main.py` monolith, simple RTSP loop, mock-first stubs) if it conflicts |
| Shared **JSON contract** `AnalysisResult` (align Swift if Lucian changes fields) | Duplicate “second backend” on main |
| iOS client that talks to **his** public Daytona URL | Hardcoding old scaffold URLs/paths |

**Rule of thumb:** Lucian owns cloud code. Brian owns iOS. Kenji helps deploy Lucian’s stack. On conflict → **Lucian wins on backend.**

---

## Product goal (not “one screenshot”)

Judges / real use need the agent to see **change over time** (leak dripping, flow starting, breaker flicking).

| Mode | Enough for? |
|------|-------------|
| Single screenshot `POST /analyze` | Static ID: “this is a Rinnai / ELCB is here” |
| **Continuous samples every 1–2 s** | Dynamic: “water is still dripping at the joint” → better steps |

**Target cadence:** about **1 frame per 1–2 seconds** (≈ 0.5–1 fps), **not** 30 fps video upload.

Why not full video stream to the LLM every frame?
- Cost / latency
- Kimi/VL models take a still (or short burst) per call
- AR still needs time to place pins; 1–2 s is fine for demo

---

## How continuous input works (two equivalent paths)

Both paths feed the **same** agent and return **`AnalysisResult`** for Brian’s AR.

### Path A — RTSP (IP camera / MediaMTX / NVR)

```text
IP cam  --rtsp://host:554/...-->  Daytona (Lucian)
                                    every 1–2s: grab frame (ffmpeg)
                                    → vision + reason (Qwen-VL / Kimi / …)
                                    → AnalysisResult
iPhone AR  <-- poll WS/REST latest --  place/update LiDAR anchors
```

- **RTSP** = how the **server** gets a live source (CCTV-style).
- Phone does **not** have to be the RTSP server.
- Best when the scene is fixed and the cam always sees the pipe/heater.

### Path B — Phone as the “camera” (1–2 s JPEG events)

```text
iPhone AR camera  --every 1–2s JPEG-->  Daytona (Lucian REST or WS /live)
                                         → same agent
iPhone  <-- AnalysisResult --  place/update anchors
```

- Same **temporal** idea as RTSP sampling; source is the Pro’s camera.
- Matches Lucian’s “Gemini-Live-style, ~1 fps JPEG” plan + optional `WS /live/{sessionId}`.
- Best for **LiDAR co-located** demo (same phone that pins in 3D).

**For the hackathon demo on 17 Pro, Path B is usually primary; Path A is the “real CCTV / RTSP” sponsor story if they have a cam URL.**

---

## What “proper fix” needs from continuous analysis

Each 1–2 s cycle should ideally produce:

1. **Updated `issues`** — e.g. “active drip observed”, “leak continues”  
2. **Stable or refined `arAnnotations`** — pin stays on joint / ELCB (don’t jump wildly)  
3. **`repairSteps`** that match what was observed over time  
4. Optional **TTS** via Lucian’s `/speech/synthesize` when the diagnosis **changes** (not every tick)

Debounce on iOS/backend:
- Don’t re-place AR if coords barely moved  
- Don’t re-speak every 2 s — only on meaningful change / user ask  

---

## Ownership

| Who | Continuous analysis work |
|-----|---------------------------|
| **Lucian** | Agent that accepts ongoing frames (REST batch or **WS live**); optional RTSP ingest in **his** backend; 1–2 s server-side sample if RTSP; no silent mock on live fail |
| **Brian** | Keep AR session up; capture JPEG every **1–2 s**; send to Lucian API/WS; apply latest `AnalysisResult` to anchors; barge-in stop audio |
| **Kenji** | Deploy Lucian’s API publicly; smoke continuous endpoint; docs — **no Xcode** |

---

## iOS behavior (Brian) — target loop

```text
Start continuous mode
  sessionId = …
  loop every 1.5–2.0 s (skip if previous request in flight):
    jpeg = snapshot from ARView (compressed)
    send to Lucian (WS event or POST)
    on result:
      placeAnnotations / update if changed
      if issues meaningfully changed → optional TTS
Stop continuous mode → keep last anchors
```

One-shot **Scan** remains for heater ELCB reliability if continuous is flaky.

---

## Lucian API shape (align to *his* OpenAPI when merged)

Prefer whatever he ships, e.g.:

- One-shot: `POST /analyze` `{ symptom, deviceHint, imageBase64 }`  
- Continuous: `WS /live/{sessionId}` with frame + transcript events (his plan)  
- Or interim: repeated `POST /analyze` every 2 s with same `sessionId` if he adds it  

**Do not** require Brian’s old `/stream/rtsp/*` routes after Lucian merge — reimplement RTSP **inside Lucian’s** architecture if needed, or drop if WS+phone frames cover the demo.

---

## Implementation status (Brian + Lucian)

| Path | Status |
|------|--------|
| Phone **WS `/live/{id}`** 1–2s frames + auto-utterance | ✅ `LiveSessionClient` + ContentView **Live** |
| Server **RTSP** sample every 1–2s → agent | ✅ `POST /rtsp/start`, `GET /rtsp/{id}/latest` |
| Public Daytona URL | ❌ still Lucian/Kenji deploy |

### iOS
- **Live (1–2s frames)** → `LiveSessionClient` → Lucian WS  
- Toggle **Live auto-analyze** → each frame also sends utterance (continuous agent reasoning)  
- **RTSP camera…** → starts server sampler, phone polls latest → AR  

### Backend
```bash
# RTSP (needs ffmpeg)
curl -X POST http://127.0.0.1:8000/rtsp/start \
  -H 'Content-Type: application/json' \
  -d '{"rtspUrl":"rtsp://…","intervalSec":2}'
```

## Definition of done (continuous)

- [x] Agent can receive frames over **time** (1–2 s) via phone WS or RTSP  
- [ ] At least **2–3** successive analyses proven on device against real URL  
- [x] AR re-applies pins on each analysis  
- [ ] Public Daytona / wss proven  
- [x] RTSP path in Lucian-style backend (ffmpeg)

---

## Summary

| Question | Answer |
|----------|--------|
| Keep Lucian backend, discard mine? | **Yes** on conflict |
| Screenshots only? | **No** for leak/dynamic demo |
| RTSP? | **Yes** as server-side live source; phone path ≈ same cadence without RTSP |
| How often? | **Every 1–2 seconds**, one in-flight request |
| Who builds agent? | **Lucian** |
| Who streams frames from 17 Pro? | **Brian** |
| Who deploys? | **Lucian + Kenji ops** |
