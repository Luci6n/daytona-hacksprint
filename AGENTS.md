# AGENTS.md — DaddyFix iOS + LiDAR Hackathon Guide
**For**: Lucian • Kenji • Brian  
**Mission**: Build a working 5-hour hybrid MVP of DaddyFix — iOS AR frontend (LiDAR + ARKit) + Daytona-orchestrated backend agent that uses Nosana + Oxylabs.  
**Single Source of Truth**: This file + `PRD.md` + the shared data contract below.

---

## 1. Project Goal (Read First)

We are building **DaddyFix** — a spatial AR repair assistant that uses the **iPhone 17 Pro’s LiDAR scanner** to understand real-world depth and place accurate, persistent 3D annotations on physical objects (pipes, valves, circuit breakers, etc.).

**Hero Demo (Water Heater)**:
Point the iPhone at the Rinnai water heater → LiDAR maps the scene → app places a persistent 3D arrow + highlight on the **ELCB** → calm “Daddy” voice explains the safety check → user can raycast/tap the highlighted part → see repair steps or buy replacement via x402.

Everything else is secondary to making this one flow feel magical and trustworthy.

---

## 2. Tech Stack & Architecture (Hybrid — Must Use Original Stack)

We are doing a **hybrid architecture** to satisfy both requirements:

### iOS Frontend (Thin Client)
- **Platform**: Native iOS 18+ (Xcode 16+)
- **UI**: SwiftUI
- **AR**: ARKit + RealityKit with **LiDAR** (`sceneReconstruction = .mesh`)
- **Responsibilities**: Camera + LiDAR spatial tracking, placing 3D annotations, raycasting/tapping, voice I/O, x402 payment UI

### Backend Agent Layer (Intelligence + Data)
- **Daytona**: Primary orchestration layer. Runs the "Daddy Agent" in a stateful sandbox. Handles file operations, runs Python scripts, manages conversation state, and exposes a simple API endpoint that the iOS app calls.
- **Nosana**: Decentralized GPU compute for heavier models (e.g. better vision inference, Whisper if we process voice server-side, or generating visual aids).
- **Oxylabs**: Scrapes real product manuals, current pricing, and replacement part availability for the detected model (e.g. Rinnai water heater parts).

**Communication Flow**:
iOS App → captures image + depth hints → calls simple API (hosted via Daytona sandbox) → Daytona Agent uses Oxylabs + Nosana (if needed) → returns structured `AnalysisResult` → iOS renders AR annotations + speaks guidance.

This way we **actually use the Oxylabs + Nosana + Daytona stack** while still leveraging the iPhone 17 Pro LiDAR for the spatial AR experience.

### 5-Hour Backend Strategy (Keep It Simple)
- Use **Daytona Python SDK** to spin a sandbox that runs a minimal FastAPI server.
- The sandbox has access to Oxylabs credentials and can submit jobs to Nosana.
- For the hackathon, Kenji can start with a strong local vision call (Groq/OpenAI) + Oxylabs scraping for the water heater, then wrap it in Daytona.
- iOS app calls a public URL exposed by the Daytona sandbox (or ngrok / Daytona proxy during demo).

---

## 3. Team Roles & File Ownership (Strict — No Overlap)

| Person   | Role                              | Owned Files / Groups                                      | Key Deliverables |
|----------|-----------------------------------|-----------------------------------------------------------|------------------|
| **Lucian** | **SwiftUI + Voice + Payments + Integration Owner** | `ContentView.swift`<br>`RepairGuideView.swift`<br>`VoiceManager.swift`<br>`PaymentModal.swift`<br>`x402Service.swift`<br>`AppState.swift` | Main UI screens, voice I/O, x402 flow, state management, wiring everything together, final demo script |
| **Kenji**  | **Vision + Agent Logic + Backend Owner** | `VisionService.swift` (iOS side)<br>`DaddyAgent.swift` (backend logic)<br>`Models/AnalysisResult.swift` (shared)<br>Daytona sandbox setup | Vision + agent logic (can run in Daytona), Oxylabs integration for product data, simple API endpoint for iOS app |
| **Brian**  | **ARKit + LiDAR + RealityKit Owner** | `ARViewContainer.swift`<br>`ARSessionManager.swift`<br>`RealityKitEntities.swift`<br>`RaycastManager.swift` | LiDAR session, plane detection, persistent anchors, raycasting/tapping in 3D space, placing 3D annotations from JSON coords |

**Rule**: Only the owner edits their files. If you need to change a shared model, propose it in chat and update together.

---

## 4. Project Structure (Xcode Groups)

```
DaddyFix/
├── Views/
│   ├── ContentView.swift          ← Lucian
│   ├── RepairGuideView.swift      ← Lucian
│   └── PaymentModal.swift         ← Lucian
├── AR/
│   ├── ARViewContainer.swift      ← Brian
│   ├── ARSessionManager.swift     ← Brian
│   ├── RealityKitEntities.swift   ← Brian
│   └── RaycastManager.swift       ← Brian
├── Services/
│   ├── VisionService.swift        ← Kenji
│   ├── DaddyAgent.swift           ← Kenji
│   ├── VoiceManager.swift         ← Lucian
│   └── x402Service.swift          ← Lucian
├── Models/
│   └── AnalysisResult.swift       ← Shared (Kenji starts)
├── Resources/
│   └── water-heater.jpg           ← Test asset
└── AppState.swift                 ← Lucian
```

---

## 5. Shared Data Contract (Critical — Agree in First 15 min)

Create `Models/AnalysisResult.swift`:

```swift
struct AnalysisResult: Codable {
    let detectedItem: String
    let confidence: Double
    let issues: [String]
    let arAnnotations: [ARAnnotation]
    let repairSteps: [RepairStep]
    let buyableParts: [BuyablePart]
}

struct ARAnnotation: Codable {
    let type: String          // "highlight", "arrow", "circle", "text"
    let x: Double             // normalized 0-1 (or world position later)
    let y: Double
    let z: Double?            // for 3D
    let width: Double?
    let height: Double?
    let label: String
    let color: String?
}

struct RepairStep: Codable {
    let step: Int
    let instruction: String
    let safetyNote: String?
}

struct BuyablePart: Codable {
    let id: String
    let name: String
    let estimatedPrice: String
    let x402Ready: Bool
}
```

**Note for Brian**: Start by supporting 2D normalized coordinates on the captured frame for quick demo. Upgrade to true 3D world positions using LiDAR raycasting + RealityKit anchors once the basic flow works. The backend (Kenji) will provide the coordinates.

---

## 6. 5-Hour Execution Plan (Parallel)

### Hour 0 (0:00–0:15) — Setup & Contract
- One person creates Xcode project from **Augmented Reality App** template (RealityKit + SwiftUI).
- Push to GitHub.
- All clone and agree on the `AnalysisResult` model above.
- Brian starts AR session + LiDAR config.
- Kenji starts VisionService + Daddy prompt.
- Lucian starts AppState + basic SwiftUI shell.

### Hours 1–2 (Parallel Deep Work)
- **Brian**: Get LiDAR session running, detect horizontal/vertical planes, implement raycasting on tap, create simple RealityKit Entity (sphere or text) that can be placed.
- **Kenji**: Build `VisionService` that takes a captured image (or base64) and returns `AnalysisResult`. Hardcode excellent result for the water heater image first. Write strong "Daddy" safety-first prompt.
- **Lucian**: Build `ContentView` with camera/AR view placeholder, voice start/stop buttons, and state machine (`idle → analyzing → showingAR → voiceGuidance`).

### Hour 2:30 — Sync
- Quick standup: Show what each has working.
- Confirm JSON contract still works.
- Decide if we mock vision with local JSON for demo reliability.

### Hours 3–4 (Integration)
- Brian exposes a method to place annotations from `arAnnotations` array.
- Lucian connects camera capture → VisionService → updates UI state → tells Brian to render annotations.
- Lucian adds voice: when analysis arrives, auto-speak the first repair step.
- Add raycast → select part → open `PaymentModal` (Lucian).

### Hour 4:30–5:00 (Polish & Demo)
- Make sure annotations stay anchored when moving phone (LiDAR win).
- Test full flow on the physical water heater or the photo.
- Lucian writes `README.md` with exact demo script.
- Deploy/TestFlight or just run on device for judges.

---

## 7. Key Implementation Notes

### For Brian (ARKit/LiDAR)
- Use `ARWorldTrackingConfiguration` + `sceneReconstruction = .mesh` to enable LiDAR.
- Start simple: Place annotations relative to detected planes.
- Raycasting: Use `ARView.raycast(from: CGPoint, allowing: .estimatedPlane, alignment: .any)`.
- Persistent anchors: Use `ARAnchor` + RealityKit `AnchorEntity`.
- For demo speed: Place annotations in world space using estimated plane + depth from LiDAR.

### For Kenji (Vision + Agent)
- Vision prompt should return both **what to say** and **where to draw** in normalized image coordinates (or world coords if possible).
- Safety is non-negotiable: Every response must include risk level and “call a licensed professional if unsure”.
- For the hackathon, make the water heater response perfect even if other items are generic.

### For Lucian (Integration + Voice + Payments)
- Use `@Observable` class for `AppState`.
- Voice: `AVSpeechSynthesizer` is zero-setup and good enough.
- x402: Show a nice modal that mimics the 402 flow (headers, payment required, success with tx hash). Real on-chain only if everything else is solid.
- Keep the UI calm and trustworthy (soft greens, blues, clear typography).

---

## 8. Demo Script for Judges (Memorize This)

1. Open DaddyFix on iPhone 17 Pro.
2. Point camera at the water heater installation.
3. Say: “Watch how LiDAR helps us understand depth…”
4. App detects the unit and places a clear 3D arrow + highlight on the ELCB.
5. Calm male voice starts: “First safety step — the Earth Leakage Circuit Breaker. I’ve highlighted it…”
6. Walk around the heater — annotation stays locked in place (LiDAR magic).
7. Tap the highlighted ELCB → “This is the safety switch. Would you like me to guide you through checking it or show replacement options?”
8. Tap “Buy replacement” → x402-style payment modal appears and succeeds.
9. End with: “This is what home repair looks like when your phone can actually see in 3D.”

---

## 9. Non-Negotiables

- **Safety first** in every voice line and UI text.
- **LiDAR must be visibly used** (mention depth / spatial understanding in demo).
- No one works on another person’s files without discussion.
- If something is taking too long, mock it cleanly and note it (better working demo than broken advanced feature).
- Test on real device early (simulator has no LiDAR).

---

## 10. Quick Commands

```bash
# After cloning
open DaddyFix.xcodeproj
```

**First commit message example**:
```
feat: initial ARKit + LiDAR session + basic raycast (Brian)
```

---

**You now have everything you need.**  
Read `PRD.md` for the “why”. Use this `AGENTS.md` for the “how” and “who does what”.

Let’s build something that feels like magic in 5 hours. Go!