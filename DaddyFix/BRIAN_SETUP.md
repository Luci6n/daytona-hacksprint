# Brian — Local Setup (ARKit + LiDAR)

You own the AR layer. This guide gets **DaddyFix** running on a **real LiDAR iPhone** so you can place persistent annotations.

> Simulator has **no LiDAR**. Always test on device.

---

## 0. What was scaffolded for you

```
daytona-hacksprint/
└── DaddyFix/
    ├── DaddyFix.xcodeproj          ← open this
    ├── BRIAN_SETUP.md              ← this file
    └── DaddyFix/
        ├── DaddyFixApp.swift
        ├── Info.plist              ← camera permission already set
        ├── Assets.xcassets
        ├── AR/                     ← YOUR files
        │   ├── ARSessionManager.swift
        │   ├── ARViewContainer.swift
        │   ├── RaycastManager.swift
        │   └── RealityKitEntities.swift
        ├── Models/
        │   └── AnalysisResult.swift   ← shared contract (+ water heater mock)
        └── Views/
            └── ContentView.swift      ← temp host (Lucian replaces later)
```

### Your public integration API

```swift
// Lucian / Kenji will call these:
raycastManager.placeAnnotations(analysis.arAnnotations)
raycastManager.clearAnnotations()
raycastManager.onAnnotationSelected = { label in /* open guide / buy */ }

// SwiftUI embed:
ARViewContainer(
    sessionManager: sessionManager,
    raycastManager: raycastManager,
    showMeshOverlay: true,          // demo: “watch LiDAR map the scene”
    autoPlaceMockAnnotations: true  // local testing only
)
```

---

## 1. Mac software you need

| Tool | Why | How |
|------|-----|-----|
| **macOS** recent | Xcode 16+ | Already on your machine |
| **Xcode 16+** (full app, not only CLI tools) | Build/run iOS | Mac App Store → “Xcode” → install (~10+ GB) |
| **Xcode Command Line Tools** | Optional extras | `xcode-select --install` |
| **Apple ID** | Free device signing | System Settings or Xcode login |

### Point CLI at full Xcode (after install)

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -license accept
xcodebuild -version   # should print Xcode 16.x (or newer)
```

If you only have Command Line Tools, `xcodebuild` will error with  
`requires Xcode, but active developer directory is a command line tools instance`.

---

## 2. Hardware you need

| Item | Required? | Notes |
|------|-----------|--------|
| **iPhone with LiDAR** | **Yes for hero demo** | iPhone 12/13/14/15/16/17 **Pro / Pro Max** (or Pro models with LiDAR) |
| USB-C / Lightning cable | Yes | Trust computer on first plug-in |
| Free disk space | ~20 GB | Xcode + derived data |

Without LiDAR the app still runs (plane-only), but the mesh / depth story is weaker for judges.

---

## 3. Open & sign the project (5 minutes)

```bash
cd /path/to/daytona-hacksprint
open DaddyFix/DaddyFix.xcodeproj
```

In Xcode:

1. Select the **DaddyFix** project (blue icon) → target **DaddyFix**
2. **Signing & Capabilities**
   - ☑ Automatically manage signing
   - **Team**: your Apple ID personal team (Add Account… if empty)
   - Bundle ID is `com.daddyfix.app` — if taken/conflict, change to  
     `com.YOURNAME.daddyfix`
3. Set run destination to your **physical iPhone** (not “Any iOS Simulator”)
4. iPhone: Settings → Privacy & Security → Developer Mode → **On** (iOS 16+), reboot if asked
5. First run: on phone tap **Trust** / enable developer app in Settings → General → VPN & Device Management

Press **⌘R** to build & run.

On first launch, accept **Camera** permission  
(copy is already in `Info.plist`).

---

## 4. What you should see (smoke test)

1. Coaching overlay: move the phone to detect a plane  
2. Status chip: **LiDAR ready** on Pro devices  
3. After ~2s, **mock ELCB** highlight + arrow may appear (auto mock)  
4. Or tap **Place mock ELCB**  
5. Toggle **LiDAR mesh** — scene understanding overlay (demo line)  
6. Walk around — annotations should **stay locked**  
7. Tap the highlight — status shows `Selected: ELCB`  
8. Tap empty surface — orange debug sphere (raycast works)

If tracking says **limited**, improve lighting and move slowly; avoid blank walls.

---

## 5. Your coding focus (after setup)

| Priority | Task | File |
|----------|------|------|
| P0 | LiDAR session stable on device | `ARSessionManager.swift` |
| P0 | Place annotations from `ARAnnotation` | `RaycastManager.swift` |
| P0 | Arrow / highlight / text look good on heater | `RealityKitEntities.swift` |
| P0 | Tap → select label callback | `RaycastManager` + `ARViewContainer` |
| P1 | Mesh toggle for demo narration | already wired |
| P1 | Tune mock coords to real Rinnai photo/unit | `AnalysisResult.waterHeaterMock` (coord with Kenji) |

**Do not** rewrite Lucian’s final UI or Kenji’s vision backend — only embed points above.

---

## 6. Common fixes

### “Failed to prepare device” / signing
- Pick a Team, unique Bundle ID, unplug/replug phone, unlock phone

### Black screen / no camera
- Check Camera permission for DaddyFix in iOS Settings  
- Confirm destination is a **device**, not simulator

### “AR not available”
- Device too old / no ARKit — need iPhone with A-series ARKit support

### `isLiDARAvailable == false` on Pro
- Rare on simulator destinations — switch to real Pro  
- Confirm iOS 18+ and world tracking supported

### Build errors about Swift concurrency / MainActor
- Use Xcode 16+, deployment **iOS 18.0** (already set)

### Annotations float wrong place
- Warm up planes 2–3s before place  
- Point at a textured vertical surface (the heater)  
- Adjust mock `x,y` in `AnalysisResult.waterHeaterMock`

---

## 7. Git hygiene (team)

```bash
# From repo root after your first working AR run:
git add DaddyFix
git commit -m "feat: initial ARKit + LiDAR session + basic raycast (Brian)"
```

Only commit **your** AR work (and shared model if the team agreed).  
Coordinate with Lucian before changing final `ContentView` ownership long-term.

---

## 8. Demo lines you enable

When judges watch:

1. Toggle **LiDAR mesh** → “Watch how LiDAR maps depth…”  
2. Place annotations → arrow locked on ELCB  
3. Walk around → “Annotation stays locked — that’s LiDAR + world tracking”  
4. Tap ELCB → hand off to Lucian’s guide / x402

---

## 9. Checklist before stand-up

- [ ] Xcode 16+ installed, `xcode-select` points at Xcode.app  
- [ ] App runs on **LiDAR iPhone**  
- [ ] Camera permission OK  
- [ ] Status shows **LiDAR ready**  
- [ ] Mock ELCB place + walk-around stability  
- [ ] Tap selects label  
- [ ] You know how Lucian embeds `ARViewContainer`

You’re set. Build on device early; polish visuals second.
