# DaddyFix PRD
**AI-Powered Spatial AR Home Repair Assistant ("Daddy Agent")**  
**Version**: 0.1 – 5-Hour Hackathon MVP  
**Date**: July 18, 2026  
**Platform**: iOS 18+ on iPhone 17 Pro (LiDAR + ARKit)

---

## 1. Executive Summary

**DaddyFix** is a hybrid iOS + backend system that uses the **iPhone 17 Pro’s LiDAR scanner + ARKit** to turn your phone into a wise, spatial-aware home repair companion.

Point your camera at a broken appliance, leaking pipe, or water heater. The app uses **LiDAR + ARKit** for accurate spatial understanding, overlays **persistent 3D AR annotations** anchored to real-world objects, and guides you step-by-step with a calm “Daddy” voice persona.

The intelligence layer runs on the required stack:
- **Daytona** orchestrates the agent
- **Nosana** provides decentralized GPU power
- **Oxylabs** scrapes real product data and manuals

Users can **raycast/tap** on any part in AR space to identify it and buy the correct replacement via **x402** payments.

**Core demo flow** (water heater example):
- Point at Rinnai water heater → LiDAR maps the scene
- App detects the unit + highlights the **ELCB** with a persistent 3D arrow + label
- Voice says: “First safety check — the Earth Leakage Circuit Breaker here may have tripped…”
- User can tap the highlighted area → see repair steps or buy replacement

---

## 2. Problem & Opportunity

Homeowners waste time and money because:
- Manuals are confusing and lack spatial context
- It’s hard to know exactly which part is failing
- Buying the correct replacement part is error-prone
- Existing tools are either generic or require remote experts

**Opportunity**: iPhone 17 Pro LiDAR enables true spatial AR. Combined with the Daytona + Nosana + Oxylabs stack for intelligence and real product data, we can deliver a trustworthy, magical repair assistant.

---

## 3. Solution Overview

**DaddyFix** uses a **hybrid architecture**:

### Frontend (iOS)
- SwiftUI + ARKit + RealityKit + **LiDAR**
- Spatial 3D annotations, raycasting, voice, and x402 UI

### Backend Agent Layer (Required Stack)
- **Daytona**: Orchestrates the “Daddy Agent” in stateful sandboxes
- **Nosana**: Heavy AI inference (vision, Whisper, etc.)
- **Oxylabs**: Scrapes manuals, pricing, and replacement parts

**Data Flow**:
iOS captures image → calls Daytona API → Agent uses Oxylabs + Nosana → returns structured `AnalysisResult` (AR coordinates + steps + buyable parts) → iOS renders AR + speaks.

---

## 4. Target Users

- Homeowners and renters who want to attempt DIY repairs confidently
- Tech-comfortable users who are not plumbing/electrical experts
- Especially valuable for first-time homeowners

---

## 5. Key MVP Features (5-Hour Scope)

| Feature                        | Description                                                              | Priority |
|--------------------------------|--------------------------------------------------------------------------|----------|
| LiDAR + ARKit Session          | Real-time depth, plane detection, world tracking                         | P0       |
| Spatial AR Annotations         | Persistent 3D highlights, arrows, labels anchored to real objects        | P0       |
| Product & Issue Detection      | Identify model + visible problems (e.g. tripped ELCB)                    | P0       |
| Raycast / Tap to Select        | Tap in AR space to select real-world part                                | P0       |
| Voice Guidance                 | Calm “Daddy” persona voice for step-by-step instructions                 | P0       |
| Repair Steps + Safety          | Numbered steps + strong safety warnings + “call pro” recommendations     | P0       |
| Tap to Buy + x402              | Select part → show correct replacement + x402 payment flow               | P1       |

**Out of Scope**:
- Complex multi-hour repairs
- Gas/high-voltage work
- Full offline mode
- Community features

---

## 6. Success Metrics

- Full water heater demo works in < 60 seconds
- AR annotations stay anchored when moving the phone (LiDAR advantage visible)
- User can raycast/tap a part and trigger buy flow
- Voice is clear and safety-first
- Demo feels magical and trustworthy

---

## 7. Risks & Mitigations

- **Safety**: Extremely conservative prompts + strong disclaimers
- **Tracking loss**: Graceful fallback to 2D + re-anchor
- **Time**: Strict scope — prioritize core AR + vision + voice flow
- **Backend complexity**: Use Daytona sandbox + simple FastAPI; mock where needed for demo reliability

---

## 8. Technical Architecture (Hybrid — Uses Required Stack)

**iOS Frontend**
- Native iOS + SwiftUI + ARKit + RealityKit + LiDAR

**Backend Agent Layer**
- **Daytona**: Main orchestration + stateful agent sandbox + simple API
- **Nosana**: Heavy GPU inference when needed
- **Oxylabs**: Product manuals, pricing, and part availability scraping

**Communication**
iOS → Daytona-hosted API → Agent (Oxylabs + Nosana) → structured JSON → iOS renders AR

---

## 9. Example Scenario (Water Heater)

User points iPhone at the Rinnai installation.

**Expected behavior**:
1. LiDAR maps the scene
2. Detects Rinnai water heater
3. Places persistent 3D highlight + arrow on the ELCB
4. Voice: “I see your Rinnai tankless water heater. The most common first check is the Earth Leakage Circuit Breaker — I’ve highlighted it…”
5. User walks around → annotation stays locked
6. Taps highlighted area → shows steps or buy option

This is the hero demo.

---

*End of PRD*