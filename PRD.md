# DaddyFix PRD
**AI-Powered Spatial AR Home Repair Assistant ("Daddy Agent")**  
**Version**: 0.2 – Hackathon MVP + Live Continuous Analysis  
**Date**: July 18, 2026  
**Platform**: iOS 18+ on iPhone 17 Pro (LiDAR + ARKit)  
**Cloud stack**: Daytona + Kimi (Moonshot) + Nosana + Oxylabs  

**Single source of truth for status & task split**: this file + `AGENTS.md`.

---

## 1. Executive Summary

**DaddyFix** turns the iPhone 17 Pro into a spatial repair companion:

1. **On device** — LiDAR + ARKit track the real world and pin 3D annotations.  
2. **In the cloud** — Daytona runs the Daddy Agent; Kimi reasons on frames; Oxylabs fetches parts; Nosana can take heavy GPU work.  
3. **Continuous demo mode** — the app can **stream analysis events** (periodic frames / short clips) so the agent can reason about **live** situations (e.g. water leaking from a pipe), not only a single snapshot.

**Hero demos for judges**
| Demo | Story |
|------|--------|
| **A — Water heater (static)** | Point at Rinnai → one analyze → ELCB highlight locked in LiDAR → voice → tap → buy |
| **B — Live event (continuous)** | Point at pipe/fixture → live frame events to Daytona → agent updates issues/annotations as the real-world event unfolds |

---

## 2. Problem & Opportunity

Homeowners waste time and money because:
- Manuals lack **spatial** context  
- It’s hard to know **which part** is failing  
- **Dynamic** failures (leaks, drips, trip/reset) need watching over time, not one photo  
- Buying the right part is error-prone  

**Opportunity**: LiDAR for true 3D lock + cloud agents (Daytona/Nosana/Oxylabs/Kimi) for reasoning + optional **live event stream** so the agent can follow what’s happening in the room.

---

## 3. Solution Overview

### Hybrid architecture (non-negotiable)

```text
iPhone 17 Pro (thin client)                    Cloud (Daytona sandbox)
─────────────────────────                      ─────────────────────────
LiDAR / ARKit / RealityKit                     FastAPI Daddy Agent
Capture frame OR live event stream    HTTPS    ├─ Kimi vision (primary)
placeAnnotations(arAnnotations)     ◄───────►  ├─ Oxylabs (parts/manuals)
Voice + x402 UI                                └─ Nosana (heavy GPU optional)

Secrets (API keys) stay in Daytona only — never in the iOS app.
```

### Two analysis modes

| Mode | When | iOS sends | Agent returns |
|------|------|-----------|----------------|
| **One-shot `/analyze`** | Water heater / “Scan once” | 1 JPEG base64 | Full `AnalysisResult` |
| **Live stream events** | Leak / continuous demo | Frames on interval (or short clip batches) + `sessionId` | Same `AnalysisResult` (or delta) → AR updates |

AR does **not** stream meshes to the cloud. Only **media + session metadata**. LiDAR keeps pins locked between agent replies.

---

## 4. Target Users

- Homeowners / renters attempting DIY with confidence  
- Tech-comfortable non-experts  
- First-time homeowners especially  

---

## 5. Feature Status vs Original MVP (Honest Ship Board)

Legend: ✅ done · 🟡 partial / scaffold · ❌ not started · ⚠️ blocked on teammate/env

### 5.1 Original PRD features

| Feature | Pri | Status | Notes |
|---------|-----|--------|--------|
| LiDAR + ARKit session | P0 | ✅ | `ARSessionManager` — mesh, planes, tracking UI; works on **real 17 Pro** |
| Spatial AR annotations | P0 | ✅ | Highlight / arrow / text entities + world anchors |
| Raycast / tap to select | P0 | ✅ | Tap annotation → label callback; surface debug spheres |
| Product & issue detection | P0 | 🟡 | Contract + mock perfect; **Kimi** wired in backend scaffold; needs Daytona public URL + live keys on sandbox |
| Repair steps + safety | P0 | 🟡 | In mock + prompt; voice readout not fully polished |
| Voice guidance | P0 | ❌ | `VoiceManager` not built — assign Kenji (spec) / Brian (if Xcode-only) |
| Tap to buy + x402 | P1 | ❌ | `PaymentModal` / `x402Service` not built |
| Daytona public API | P0 | 🟡 | `backend/` FastAPI ready to deploy; **not yet proven on Daytona URL** |
| Oxylabs | P0/P1 | 🟡 | Stub client; needs credentials + real scrape |
| Nosana | P1 | 🟡 | Stub client; optional GPU path |
| Kimi vision | P0 | 🟡 | `vision.py` Moonshot-compatible; model `kimi-k2.7-code` (verify id on deploy) |

### 5.2 New judge-facing feature (v0.2)

| Feature | Pri | Status | Owner |
|---------|-----|--------|--------|
| **Live stream analysis events** | **P0 for continuous demo** | ❌ → next | **Brian (iOS capture + event bus)** + **Lucian (Daytona ingest + agent)** |
| Live AR annotation refresh | P0 | ❌ | Brian — re-`placeAnnotations` / update anchors on each agent event |
| Session continuity (`sessionId`) | P0 | ❌ | Shared contract — Lucian API + Brian client |

### 5.3 Integration / product chrome

| Feature | Status | Notes |
|---------|--------|--------|
| `AnalysisResult` shared contract | ✅ | Swift + Python models aligned (camelCase) |
| iOS `VisionService` one-shot client | 🟡 | Exists; points at `APIConfig.baseURL` (must become Daytona URL) |
| AppState + ContentView shell | 🟡 | Temporary Brian shell; Kenji designs polish |
| Demo reliability mock | ✅ | Local + `GET /analyze/mock` |

---

## 6. Live / Continuous Events — Why Screenshots Fail + RTSP

### Goal for judges
Show: *“While something is happening in the real world (e.g. a tap leaking), the agent watches **over time** and updates AR guidance.”*

A **single screenshot cannot** reliably prove a drip/leak: you need **temporal** evidence (multiple frames from a stream).

### Two ingest paths (both end in the same `AnalysisResult`)

| Path | Source | Who pulls media | Best for |
|------|--------|-----------------|----------|
| **A — RTSP** | IP / CCTV camera (`rtsp://…:554/…`) | **Daytona** samples with ffmpeg every N s | Real continuous events, fixed scene, pro story |
| **B — Phone events** | iPhone AR camera JPEGs | **Phone POSTs** every N s | LiDAR co-located view, no extra camera |

```text
                    ┌─ RTSP IP cam ──ffmpeg sample──┐
Real world event ──┤                               ├─► Daytona Daddy Agent (Kimi)
                    └─ iPhone frame events ─────────┘         │
                                                              ▼
                                                     AnalysisResult JSON
                                                              │
                     iPhone LiDAR AR ◄── place/update annotations (poll or response)
```

**RTSP** = control protocol for play/pause/describe of media (classic CCTV; often port **554**).  
Actual video bytes usually ride **RTP**; we use **ffmpeg** to grab JPEG snapshots from the live RTSP URL on an interval so the model sees *change over time* without full WebRTC.

### API (implemented in `backend/`)

| Method | Path | Role |
|--------|------|------|
| POST | `/stream/rtsp/start` | `{ rtspUrl, intervalSec, hint }` → sessionId; server loops |
| POST | `/stream/phone/start` | Open phone-driven session |
| POST | `/stream/phone/event` | `{ sessionId, seq, imageBase64 }` |
| GET | `/stream/{sessionId}/latest` | Latest result for AR |
| POST | `/stream/{sessionId}/stop` | Stop |

### Demo defaults

| Parameter | Value |
|-----------|--------|
| Sample interval | **2.0 s** |
| JPEG quality | moderate (q≈5 ffmpeg / 0.55 phone) |
| Max in-flight (phone) | 1 |
| Daytona dep | **ffmpeg** (`/health.ffmpeg`) |

### What this is **not**
- Not streaming LiDAR meshes to cloud  
- Not 60 fps AI on every AR frame  
- Not requiring the **iPhone to be an RTSP server** (hard / unnecessary)  
- Optional later: WebRTC, full video clip upload, Nosana video models  

### Brian vs Lucian on live

| Brian | Lucian |
|-------|--------|
| Phone capture timer → `/stream/phone/event` | Deploy + **ffmpeg** + RTSP URL demo |
| Poll `/latest` OR use POST response → AR | Harden RTSP + Kimi on continuous frames |
| Optional UI: “Start RTSP session” with URL | Provide demo cam URL or MediaMTX |

---

## 7. Success Metrics (Judges)

| Metric | Target |
|--------|--------|
| Water heater one-shot demo | &lt; 60s, ELCB locked while walking |
| Live stream demo | ≥ 2 agent updates while pointing at scene; annotations refresh |
| Stack story | Can say “Daytona hosts agent; Kimi sees; Oxylabs parts; Nosana GPU path” |
| Safety | Every spoken/shown path has pro disclaimer |
| Reliability | Mock path works if cloud blips |

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Live stream latency / cost | 2s interval, single in-flight, JPEG compress |
| Kimi timeout | Fall back to last good result + mock |
| Daytona URL not ready | LAN FastAPI for dev; mock for AR; ship URL ASAP |
| Kenji Xcode blocked | Brian verifies all device builds; Kenji delivers UI copy/specs/Swift as files |
| Tracking loss | Re-raycast on new events; coaching overlay |
| Safety | Conservative prompts; never DIY gas/high voltage |

---

## 9. Technical Architecture

### iOS
- ARKit + RealityKit + LiDAR  
- `VisionService` — one-shot + **live event client**  
- `LiveAnalysisSession` (Brian) — timer, capture, seq, apply results to AR  

### Cloud (Daytona)
- FastAPI:  
  - `POST /analyze` — one-shot  
  - `GET /analyze/mock` — hero JSON  
  - `POST /analyze/stream/event` — live frame event (**to implement**)  
  - `GET /health`  
- Agent pipeline: Kimi → (Nosana optional) → Oxylabs enrich → `AnalysisResult`  

### Shared contract (`AnalysisResult`)
Unchanged fields for both one-shot and live. Optional future fields:
- `sessionId`, `seq`, `eventType` (`"snapshot" | "live"`) — add when stream lands  

---

## 10. Example Scenarios

### A — Water heater (one-shot) — original hero
1. LiDAR maps scene  
2. Tap Analyze → one frame → Daytona/Kimi  
3. ELCB highlight + arrow locked  
4. Voice step 1  
5. Walk around → pins stay  
6. Tap → steps / buy  

### B — Live leak / continuous event — v0.2 hero
1. Start **Live Analyze**  
2. Phone sends frame events every ~2s to Daytona  
3. Agent: “I see moisture / drip near the joint…” updates issues + annotation  
4. AR re-pins or updates label in world space  
5. Stop stream → last state remains anchored  

---

## 11. Task Distribution (Three People) — Current Truth

> **Platform reality**: Lucian = Windows (backend only). Kenji = Mac but **Xcode may be blocked** → deliver specs/Swift PRs; **Brian verifies on device**. Brian = Mac + **working 17 Pro + Xcode**.

### ✅ Already done (mostly Brian + shared scaffold)

| Done | Who |
|------|-----|
| Xcode project, LiDAR session, mesh toggle | Brian |
| AR entities, raycast, placeAnnotations, tap select | Brian |
| On-device run proven on iPhone 17 Pro | Brian |
| `AnalysisResult` Swift + Python | Shared |
| Backend scaffold: FastAPI, Kimi vision path, Oxylabs/Nosana stubs, mock | Brian scaffold (Lucian owns deploy/hardening) |
| iOS `VisionService` + `APIConfig` + AppState shell | Brian (temporary takeover) |

### 🔴 Brian — ship next (AR + live stream + device truth)

| Task | Pri | Deliverable |
|------|-----|-------------|
| `LiveAnalysisSession` — capture AR frames on interval | P0 | Start/Stop Live in UI |
| POST live events to Daytona (`/analyze/stream/event` or reuse `/analyze`) | P0 | Works with Lucian’s URL |
| On each result: update AR annotations without killing tracking | P0 | Smooth refresh |
| Point `APIConfig.baseURL` at **Daytona public URL** | P0 | Demo network path |
| One-shot Analyze still works (heater) | P0 | Fallback reliability |
| Device verification of all iOS merges | P0 | Kenji/Lucian don’t block on Xcode |
| Polish entities / coords on real heater | P1 | Judge-ready look |

**Brian does not own**: Oxylabs scrape implementation, Nosana job API, Daytona provisioning (Lucian).

### 🔴 Lucian — cloud agent + stack (Windows)

| Task | Pri | Deliverable |
|------|-----|-------------|
| Deploy `backend/` on **Daytona**, public HTTPS URL | P0 | Paste URL to Brian |
| Env on sandbox: `MOONSHOT_API_KEY`, Oxylabs, Nosana | P0 | `/health` shows flags |
| Prove `POST /analyze` with real Kimi image | P0 | Real (or good) ELCB coords |
| Implement **`POST /analyze/stream/event`** (sessionId, seq, image) | P0 | Live demo backend |
| Oxylabs: real parts for Rinnai/ELCB if keys work | P1 | `buyableParts` filled |
| Nosana: call path or honest “configured/skip” in health | P1 | Stack story |
| Agent prompts: safety + live event language (“leak continuing…”) | P0 | Trustworthy Daddy voice copy in JSON |

**Lucian does not own**: Xcode / LiDAR / live capture on phone.

### 🟡 Kenji — UI / voice / payments (Mac; Xcode may fail)

| Task | Pri | Deliverable | If Xcode broken |
|------|-----|-------------|-----------------|
| VoiceManager (`AVSpeechSynthesizer`) + Daddy copy | P0 | Swift file + when to speak | Write file; Brian merges & tests |
| RepairGuideView (steps + safety) | P0 | SwiftUI | Same |
| PaymentModal + x402Service (can be simulated 402) | P1 | SwiftUI flow | Same |
| UI polish: chrome, colors, demo script README | P0 | Spec + code | Figma/notes + markdown OK |
| Wire AppState phases with Brian’s live/one-shot | P0 | Integration checklist | Pair with Brian |

**Kenji does not own**: Daytona, Oxylabs, Nosana, LiDAR internals.

---

## 12. Integration Sequence (Order of Operations)

```text
1. Lucian: Daytona up + public URL + /health + /analyze + /analyze/mock
2. Brian: APIConfig.baseURL = that URL; one-shot Analyze on 17 Pro
3. Brian + Lucian: live event endpoint + LiveAnalysisSession
4. Kenji (or Brian): voice on first repair step
5. Kenji: guide sheet + optional x402
6. Full run-through A (heater) then B (live) for judges
```

---

## 13. Out of Scope (still)

- Multi-hour repairs, gas/high-voltage DIY  
- Full offline product  
- Community / social  
- Broadcast-quality WebRTC multi-viewer (unless free time)  

---

## 14. Demo Script (Updated)

### Demo A — One-shot (safe baseline)
1. Open DaddyFix on 17 Pro  
2. “LiDAR maps depth…” (mesh toggle)  
3. Analyze → ELCB pin locks  
4. Walk around  
5. Tap → steps / buy  

### Demo B — Live continuous (differentiation)
1. “Now continuous real-world events…”  
2. Start **Live Analyze** on pipe / fixture / heater panel  
3. Show status: `seq 1…2…3` / agent updates  
4. Annotation or issue text updates as agent re-reasons  
5. Stop live → pins remain  
6. Close: “Cloud agent on Daytona watched the event; LiDAR kept it spatial.”  

---

## 15. Gap Summary (How far vs original PRD)

| Area | % ready for judges (est.) | Blocker |
|------|---------------------------|---------|
| On-device AR / LiDAR | **~85%** | Polish only |
| One-shot cloud analyze | **~40%** | Daytona deploy + Kimi prove |
| Live stream continuous | **~5%** | Not built — Brian + Lucian P0 |
| Voice + UI chrome | **~15%** | Kenji / Brian |
| Oxylabs / Nosana real calls | **~15%** | Lucian + keys |
| x402 | **~0%** | Kenji P1 |

**Bottom line**: Spatial AR foundation is the strongest completed slice. **Cloud path + live stream are the critical path to a differentiated judge demo.** One-shot heater must still work as safety net if live is flaky.

---

*End of PRD v0.2*
