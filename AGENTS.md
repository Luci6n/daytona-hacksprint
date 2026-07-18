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

### Brian (all Xcode / iOS — no Kenji Swift)
- [x] LiDAR session + annotations + tap  
- [x] On-device 17 Pro  
- [x] VisionService + VoiceManager + AppState + UI sheets  
- [x] Live WS client (1–2s frames) + RTSP client hooks  
- [ ] Set `APIConfig` to Lucian’s public Daytona URL  
- [ ] End-to-end one-shot + live on device with real URL  
- [ ] Bundle ID **`com.daddyfix.app`** / Team **Brian Har**  

### Lucian
- [ ] Daytona deploy + public URL in team chat  
- [ ] Sandbox env: Moonshot/Kimi, Oxylabs, Nosana  
- [ ] Prove `/analyze` + live WS + TTS e2e  
- [ ] Oxylabs parts for heater if possible  

### Kenji (ops only — **no Xcode, no `.swift`**)
- [ ] Smoke `/health`, `/analyze`, TTS against deployed URL  
- [ ] Help Daytona public URL (with Lucian)  
- [ ] Judge one-pager / demo script (docs only)  

---

## 6. Integration Order

1. Lucian → Daytona URL live  
2. Brian → one-shot Scan + Live on phone  
3. Full Demo A then Demo B  

---

## 7. Non-Negotiables

- Safety-first copy always  
- LiDAR visibly used  
- Cloud stack story (Daytona / Kimi / Oxylabs / Nosana)  
- Live stream = **events**, not keys on device  
- Explicit mock only if user chooses Local mock  
- Test on **real device** (no LiDAR in simulator)  
- **Kenji does not edit Swift**  

---

## 8. Quick Commands

```bash
open DaddyFix/DaddyFix.xcodeproj

# Backend (repo root, Python 3.10+)
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Bundle ID:** `com.daddyfix.app`  
**Team:** Brian Har (Personal Team)

**Commit examples**
```text
feat(ar): LiDAR session + annotation placement (Brian)
feat(live): 1-2s WS frame stream client (Brian)
feat(api): Daytona analyze + live WS (Lucian)
```

---

Ship Demo A solid first; Demo B (live) is the differentiator.
