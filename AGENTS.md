# AGENTS.md — DaddyFix iOS + LiDAR Hackathon Guide
**For**: Lucian • Kenji • Brian  
**Mission**: Hybrid MVP — iOS LiDAR AR + Daytona cloud agent (Kimi + Nosana + Oxylabs) + **live analysis events** for continuous real-world demos.  
**Single Source of Truth**: This file + `PRD.md` v0.2.

> **Platform note**: Lucian = **Windows** (backend / Daytona only). Kenji + Brian = **Mac**. Kenji’s Xcode may be blocked → Brian is **device verifier** and temporary owner of shippable iOS integration. Brian also owns **live stream capture** on device.

---

## 0. Status Board (read first)

| Area | Status | Owner going forward |
|------|--------|---------------------|
| LiDAR + AR anchors + tap | ✅ Done on device | Brian |
| One-shot `VisionService` + mock | 🟡 Scaffold | Brian client / Lucian API |
| Backend FastAPI + Kimi path | 🟡 Scaffold in repo | **Lucian deploy + harden** |
| Daytona **public URL** | ❌ | **Lucian** |
| Live stream events | ❌ | **Brian (iOS) + Lucian (API)** |
| Voice + Repair UI + x402 | ❌ | Kenji (Brian merges if needed) |
| Oxylabs / Nosana real | 🟡 Stubs | Lucian |

Details & % readiness: **`PRD.md` §5, §11, §15**.

---

## 1. Project Goal

**DaddyFix** — spatial AR repair assistant on iPhone 17 Pro LiDAR + cloud Daddy Agent.

**Hero demos**
1. **One-shot**: Rinnai water heater → ELCB AR pin → voice → tap → buy  
2. **Live**: continuous frame **events** to Daytona while a real-world event unfolds (e.g. leak) → agent re-analyzes → AR updates  

---

## 2. Architecture (Cloud + Device)

```text
iPhone                              Daytona (public HTTPS)
─────                               ─────────────────────
LiDAR / AR                          FastAPI Daddy Agent
One-shot POST /analyze      ──►     Kimi (Moonshot) vision
Live  POST /analyze/stream/event ►  Oxylabs parts
placeAnnotations(JSON)      ◄──     Nosana optional GPU
```

- **Keys never on phone.**  
- Local uvicorn = dev only. Demo = Daytona URL in `APIConfig.baseURL`.  
- Live mode = **periodic JPEGs + sessionId**, not 60fps WebRTC (unless free time).

---

## 3. Roles & Ownership (updated)

| Person | Platform | Owns now | Does not own |
|--------|----------|----------|--------------|
| **Brian** | Mac + 17 Pro | `AR/*`, live capture/`LiveAnalysisSession`, device QA, ship `ContentView`/`AppState`/`VisionService` until Kenji unblocked | Daytona deploy, Oxylabs scrape impl |
| **Lucian** | Windows | `backend/*`, Daytona sandbox, public URL, Kimi/Oxylabs/Nosana, stream **API**, agent prompts | Xcode, LiDAR |
| **Kenji** | Mac (Xcode flaky) | Voice, RepairGuide, Payment/x402, UI copy, demo script — deliver as files/PRs | Backend secrets, AR internals |

**Rule**: Prefer discussion before editing someone else’s core files. Brian may merge Kenji’s Swift on device when Kenji can’t run Xcode.

### File map

```text
backend/                          ← Lucian
  main.py, daddy_agent.py, vision.py, models.py
  oxylabs_client.py, nosana_client.py
  POST /analyze, GET /analyze/mock
  POST /analyze/stream/event      ← Lucian to add

DaddyFix/DaddyFix/
  AR/*                            ← Brian
  Services/VisionService.swift    ← Brian (client) / contract with Lucian
  Services/APIConfig.swift        ← Brian sets Daytona URL
  Services/LiveAnalysisSession    ← Brian to add
  AppState.swift, ContentView     ← Brian ship; Kenji polish
  VoiceManager, RepairGuideView,  ← Kenji
  PaymentModal, x402Service       ← Kenji
  Models/AnalysisResult.swift     ← Shared
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
