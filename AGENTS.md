# AGENTS.md — DaddyFix iOS + LiDAR Hackathon Guide
**For**: Lucian • Kenji • Brian  
**Mission**: Hybrid MVP — iOS LiDAR AR + Daytona cloud agent (Kimi + Nosana + Oxylabs) + **live analysis events** for continuous real-world demos.  
**Single Source of Truth**: This file + `PRD.md` v0.2.

> **Platform note (current)**: Lucian = **Windows** (backend code + providers). Brian = **Mac + 17 Pro + all Xcode**. Kenji = **no Xcode** → **deploy/ops/docs/smoke tests** only, without rewriting Lucian’s agent code. See `KENJI_ASSIGNMENTS.md` + `BRIAN_IOS_TAKEOVER.md`.

---

## 0. Status Board (read first)

| Area | Status | Owner going forward |
|------|--------|---------------------|
| LiDAR + AR anchors + tap | ✅ Done on device | **Brian** |
| All iOS UI / voice / VisionService / x402 | 🟡 / ❌ | **Brian (full takeover)** |
| Backend agent / providers | 🟡 Lucian `feature/lucian-backend` | **Lucian** |
| Daytona **public URL** | ❌ | **Lucian** (+ Kenji deploy assist) |
| Live WS / continuous | ❌ / in progress | **Lucian API** + **Brian iOS client** |
| API smoke tests, judge docs, demo script | — | **Kenji** |
| Oxylabs / Nosana / TTS deploy | 🟡 | **Lucian** (+ Kenji ops assist) |

Details: **`PRD.md`**, **`KENJI_ASSIGNMENTS.md`**, **`BRIAN_IOS_TAKEOVER.md`**.

---

## 1. Project Goal

**DaddyFix** — spatial AR repair assistant on iPhone 17 Pro LiDAR + cloud Daddy Agent.

**Hero demos**
1. **One-shot**: Rinnai water heater → ELCB AR pin → voice → tap → buy  
2. **Live**: continuous frame **events** to Daytona while a real-world event unfolds (e.g. leak) → agent re-analyzes → AR updates  

---

## 2. Architecture (Cloud + Device)

```text
iPhone / IP camera                      Daytona (public HTTPS)
──────────────────                      ─────────────────────
LiDAR / AR (phone)                      FastAPI Daddy Agent
One-shot POST /analyze         ──►      Kimi vision
Phone live POST /stream/phone/event ►   Oxylabs / Nosana
RTSP cam  (server pulls)       ──►      ffmpeg sample every 2s
placeAnnotations(JSON)         ◄──      AnalysisResult (+ sessionId/seq)
```

- **Keys never on phone.**  
- **RTSP** = continuous real-world events (leaks) the model can see over time.  
- Phone does **not** need to host RTSP; either phone JPEG events **or** IP cam RTSP.  
- Live = **interval samples + sessionId**, not 60fps WebRTC (unless free time).

---

## 3. Roles & Ownership (current — Xcode all Brian)

| Person | Platform | Owns now | Does not own |
|--------|----------|----------|--------------|
| **Brian** | Mac + 17 Pro | **Entire iOS app**: `AR/*`, `VisionService`, `VoiceManager`, SwiftUI, x402, Speech, live client, device QA | Rewriting Lucian’s Python agent |
| **Lucian** | Windows | **Backend code** & providers (`feature/lucian-backend`), OpenAPI, WS live route, agent prompts | Xcode, iOS |
| **Kenji** | No Xcode | **Deploy assist**, smoke tests, env checklists, judge one-pager, demo script, Nosana TTS ops **with Lucian’s OK** | Any `.swift`; Lucian domain refactors |

**Rule**: Kenji does not collide with Lucian — no silent rewrites of agent/providers. Brian does not wait on Kenji for Swift.

### File map

```text
backend/                          ← Lucian (code)
  (+ Kenji: run deploy, smoke, docs only)

DaddyFix/DaddyFix/                ← Brian (all of it)
  AR/*
  Services/*   VisionService, VoiceManager, APIConfig, x402…
  Views/*      ContentView, RepairGuide, PaymentModal…
  AppState.swift, Models/AnalysisResult.swift
```

---

## 4. Shared Contract

`AnalysisResult` / `ARAnnotation` / `RepairStep` / `BuyablePart` — camelCase JSON.  
See `backend/models.py` + `Models/AnalysisResult.swift`.

**Live extensions (add with Lucian + Brian together):**
```json
{
  "sessionId": "uuid",
  "seq": 3,
  "eventType": "live",
  "detectedItem": "...",
  "arAnnotations": [ ... ],
  "repairSteps": [ ... ],
  "buyableParts": [ ... ]
}
```

---

## 5. Task Checklist by Person

### Brian (you)
- [x] LiDAR session + annotations + tap  
- [x] On-device 17 Pro  
- [x] VisionService one-shot + AppState shell  
- [ ] `LiveAnalysisSession` (interval capture, seq, apply AR)  
- [ ] Wire Start/Stop Live in UI  
- [ ] Set `APIConfig` to Lucian’s Daytona URL  
- [ ] End-to-end one-shot + live on device  
- [ ] Merge/test Kenji UI files  

### Lucian
- [ ] Daytona deploy + public URL in team chat  
- [ ] Sandbox env: Moonshot/Kimi, Oxylabs, Nosana  
- [ ] Prove `/analyze` with real image  
- [ ] Implement `/analyze/stream/event`  
- [ ] Oxylabs parts for heater if possible  
- [ ] Safety-first prompts for live language  

### Kenji
- [ ] `VoiceManager` + Daddy lines (safety first)  
- [ ] `RepairGuideView`  
- [ ] `PaymentModal` + x402 (can simulate)  
- [ ] Demo script README for judges  
- [ ] UI polish notes if Xcode blocked  

---

## 6. Integration Order

1. Lucian → Daytona URL live  
2. Brian → one-shot Analyze on phone  
3. Brian + Lucian → live events  
4. Kenji → voice + sheets  
5. Full Demo A then Demo B (see `PRD.md` §14)  

---

## 7. Non-Negotiables

- Safety-first copy always  
- LiDAR visibly used  
- Cloud stack story (Daytona / Kimi / Oxylabs / Nosana)  
- Live stream = **events**, not keys on device  
- Mock fallback if cloud dies mid-demo  
- Test on **real device** (no LiDAR in simulator)  

---

## 8. Quick Commands

```bash
open DaddyFix/DaddyFix.xcodeproj

# Backend local dev (not the judge path)
cd backend && source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Commit examples**
```text
feat(ar): LiDAR session + annotation placement (Brian)
feat(live): frame event stream client (Brian)
feat(api): Daytona analyze + stream event (Lucian)
feat(ui): voice + repair guide (Kenji)
```

---

Read **`PRD.md` v0.2** for full gap analysis, live-stream design, and success metrics.  
Ship Demo A solid first; Demo B (live) is the differentiator.
