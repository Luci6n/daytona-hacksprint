# DaddyFix — Daytona Hacksprint

Spatial AR home repair assistant (iOS LiDAR + ARKit + Daytona/Nosana/Oxylabs).

## Docs

- [`AGENTS.md`](./AGENTS.md) — roles, architecture, 5-hour plan  
- [`PRD.md`](./PRD.md) — product requirements  
- [`DaddyFix/XCODE_SETUP.md`](./DaddyFix/XCODE_SETUP.md) — **install Xcode + run on device** (Kenji / Brian)  
- [`DaddyFix/BRIAN_SETUP.md`](./DaddyFix/BRIAN_SETUP.md) — Brian AR smoke test & coding focus

## iOS app (Mac only)

```bash
# Full step-by-step: DaddyFix/XCODE_SETUP.md
open DaddyFix/DaddyFix.xcodeproj
```

Requires **Xcode 16+**, **iOS 18+**, and a **LiDAR iPhone** for the hero demo (simulator has no LiDAR).  
**Lucian (Windows):** skip Xcode — work on backend only.

### Team ownership

| Person | Platform | Area |
|--------|----------|------|
| **Brian** | Mac | `DaddyFix/DaddyFix/AR/*` (LiDAR + RealityKit) |
| **Kenji** | Mac | SwiftUI shell, voice, x402, `AppState`, iOS `VisionService` client |
| **Lucian** | Windows | Backend / agent / Daytona + Nosana + Oxylabs, shared JSON contract |

See [`AGENTS.md`](./AGENTS.md) for the full file ownership map.
