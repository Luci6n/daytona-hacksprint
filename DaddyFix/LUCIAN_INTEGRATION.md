# Lucian Integration Guide — Brian’s AR Layer

**From**: Brian (ARKit / LiDAR / RealityKit)  
**To**: Lucian (SwiftUI / Voice / Payments / AppState)  
**Goal**: Drop AR into your UI shell, place annotations when Kenji’s analysis arrives, handle taps → guide / buy.

You **own**: `ContentView`, `AppState`, `VoiceManager`, `PaymentModal`, `x402Service`, `RepairGuideView`.  
You **do not edit**: files under `DaddyFix/AR/*` (ask Brian).  
You **consume**: `Models/AnalysisResult.swift` (shared with Kenji).

---

## 1. What Brian already built

| Piece | Path | Your job |
|-------|------|----------|
| SwiftUI AR view | `AR/ARViewContainer.swift` | Embed full-screen under your chrome |
| Session + LiDAR | `AR/ARSessionManager.swift` | Hold as `@StateObject`, show status if you want |
| Place / tap / clear | `AR/RaycastManager.swift` | Call after analysis; handle selection |
| Visuals | `AR/RealityKitEntities.swift` | Don’t touch |
| Temp demo UI | `ARDebugHostView` in `ARViewContainer.swift` | **Replace** — do not ship as final UI |
| Shared model | `Models/AnalysisResult.swift` | Use `arAnnotations`, steps, parts |

`Views/ContentView.swift` currently hosts `ARDebugHostView` so Brian could test alone. **You replace that** with the real app shell.

---

## 2. Public API (only things you need)

### Embed

```swift
ARViewContainer(
    sessionManager: sessionManager,   // ARSessionManager
    raycastManager: raycastManager,   // RaycastManager
    showMeshOverlay: Bool,            // true = show LiDAR mesh (demo beat)
    autoPlaceMockAnnotations: false   // ALWAYS false in your app (Brian test only)
)
```

### Place / clear (from Kenji result)

```swift
// After VisionService / Daytona returns AnalysisResult:
raycastManager.placeAnnotations(result.arAnnotations)

// On reset / new scan:
raycastManager.clearAnnotations()
```

### Tap → your UI

```swift
raycastManager.onAnnotationSelected = { label in
    // label e.g. "ELCB"
    // → open RepairGuideView, speak step, or PaymentModal
}
```

### Optional status (HUD)

```swift
sessionManager.trackingStatus   // .initializing / .normal / .limited / …
sessionManager.isLiDARAvailable // Bool — show “LiDAR ready”
sessionManager.planeCount       // Int
```

---

## 3. Ownership of objects (important)

Create **once** in `AppState` (or your root view) and share:

```swift
@MainActor
@Observable
final class AppState {
    // Brian
    let sessionManager = ARSessionManager()
    let raycastManager = RaycastManager()

    // Lucian
    var phase: AppPhase = .idle
    var analysis: AnalysisResult?
    var selectedPartLabel: String?
    var showMeshOverlay = false
    var showPayment = false
    // voiceManager, etc.

    enum AppPhase {
        case idle
        case analyzing
        case showingAR
        case voiceGuidance
    }
}
```

**Rules:**
- One `ARSessionManager` + one `RaycastManager` for the whole app.
- Wire `onAnnotationSelected` in `.onAppear` of your root/ContentView (not inside AR files).
- Call `placeAnnotations` only on the **main actor** (already `@MainActor` on managers).

---

## 4. Suggested `ContentView` skeleton

```swift
import SwiftUI

struct ContentView: View {
    @State private var app = AppState()
    // or @Environment / @StateObject if you prefer older pattern

    var body: some View {
        ZStack {
            // 1) AR full bleed
            ARViewContainer(
                sessionManager: app.sessionManager,
                raycastManager: app.raycastManager,
                showMeshOverlay: app.showMeshOverlay,
                autoPlaceMockAnnotations: false
            )
            .ignoresSafeArea()

            // 2) Your chrome on top
            VStack {
                topBar
                Spacer()
                bottomBar
            }
        }
        .onAppear {
            app.raycastManager.onAnnotationSelected = { label in
                app.selectedPartLabel = label
                app.phase = .voiceGuidance
                // voiceManager.speak("This is the \(label)…")
                // optionally present RepairGuideView sheet
            }
        }
        .sheet(item: /* guide or part */) { … }
        .sheet(isPresented: $app.showPayment) {
            PaymentModal(…)
        }
    }

    // Example: after Kenji analysis succeeds
    func onAnalysis(_ result: AnalysisResult) {
        app.analysis = result
        app.phase = .showingAR
        app.raycastManager.placeAnnotations(result.arAnnotations)

        if let first = result.repairSteps.first {
            // voiceManager.speak(first.instruction)
            app.phase = .voiceGuidance
        }
    }
}
```

### Demo-only fallback (if Kenji API is down)

```swift
onAnalysis(AnalysisResult.waterHeaterMock)
```

Mock lives on `AnalysisResult` already — safe for judges if backend flakes.

---

## 5. State machine (how pieces connect)

```
idle
  → user taps “Scan” / auto-capture
analyzing
  → Kenji VisionService / Daytona → AnalysisResult
showingAR
  → you call raycastManager.placeAnnotations(result.arAnnotations)
  → Brian places persistent 3D highlight + arrow on ELCB
voiceGuidance
  → you speak repairSteps[0] (AVSpeechSynthesizer)
  → user taps ELCB in AR
  → onAnnotationSelected("ELCB")
  → show RepairGuideView OR “Buy replacement” → PaymentModal (x402)
```

| Event | Who fires | You do |
|-------|-----------|--------|
| Analysis ready | Kenji / you | `placeAnnotations` + start voice |
| Tap ELCB | Brian raycast | Open guide / buy choices |
| Buy | You | `PaymentModal` / x402 |
| New scan | You | `clearAnnotations()` then re-analyze |

---

## 6. UI chrome tips (don’t fight AR)

- Keep overlays **transparent** (`.ultraThinMaterial` capsules) — camera must stay visible.
- Prefer **portrait** (Info.plist already portrait-first).
- Don’t cover the whole screen with opaque panels during placement.
- Optional top chip: LiDAR status from `sessionManager.trackingStatus`.
- Optional toggle: `showMeshOverlay` for the line *“Watch how LiDAR maps the scene…”* (toggle on briefly, then off so labels stay readable).

---

## 7. What you should NOT do

| Don’t | Why |
|-------|-----|
| Edit `AR/*.swift` without asking Brian | Ownership + session bugs |
| Set `autoPlaceMockAnnotations: true` in production UI | Double-places with your real analysis |
| Create a second `ARView` / second session | Tracking breaks |
| Place annotations before AR has warmed (~1–2s planes) | Raycast may fall back to “in front of camera” |
| Assume tap coordinates yourself | Brian owns raycast; use the callback |

---

## 8. Data contract you share with Kenji

```swift
struct AnalysisResult {
    let detectedItem: String
    let confidence: Double
    let issues: [String]
    let arAnnotations: [ARAnnotation]  // ← Brian places these
    let repairSteps: [RepairStep]      // ← you speak / show
    let buyableParts: [BuyablePart]    // ← you + x402
}

struct ARAnnotation {
    let type: String   // "highlight" | "arrow" | "circle" | "text"
    let x, y: Double   // normalized 0…1
    let z: Double?
    let width, height: Double?
    let label: String  // e.g. "ELCB" — same string returned on tap
    let color: String?
}
```

**Tap label** is `ARAnnotation.label`. Match buyable parts / copy to that string when possible (e.g. `"ELCB"`).

---

## 9. Minimal integration checklist

- [ ] Replace `ContentView` body: `ARViewContainer` + your chrome (remove sole use of `ARDebugHostView`)
- [ ] Own `sessionManager` + `raycastManager` in `AppState`
- [ ] `autoPlaceMockAnnotations: false`
- [ ] On analysis success → `placeAnnotations(result.arAnnotations)`
- [ ] Wire `onAnnotationSelected` → guide / voice / payment
- [ ] On reset → `clearAnnotations()`
- [ ] Voice on first `repairSteps` entry (safety-first copy)
- [ ] Optional: mesh toggle bound to `showMeshOverlay`
- [ ] Device test with Brian: walk-around stability + tap ELCB → your sheet

---

## 10. Copy-paste for Slack / stand-up

> AR is ready to embed. Use `ARViewContainer(sessionManager:raycastManager:showMeshOverlay:autoPlaceMockAnnotations:)`. Hold one `ARSessionManager` + one `RaycastManager` in AppState. When analysis returns, call `raycastManager.placeAnnotations(result.arAnnotations)`. Set `onAnnotationSelected` for taps (label string, e.g. `"ELCB"`). Keep `autoPlaceMockAnnotations: false`. Don’t edit `AR/*` — ping Brian. Mock fallback: `AnalysisResult.waterHeaterMock`. Details: `DaddyFix/LUCIAN_INTEGRATION.md`.

---

## 11. Who to ping

| Issue | Person |
|-------|--------|
| Annotations don’t stick / wrong place / LiDAR | **Brian** |
| JSON / vision / Daytona API | **Kenji** |
| Voice, sheets, x402, app chrome | **Lucian** (you) |

---

*Brian’s local harness: `ARDebugHostView` — reference only, not final product UI.*
