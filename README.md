# DaddyFix — Daytona Hacksprint

Spatial AR home repair assistant (iOS LiDAR + ARKit + Daytona/Nosana/Oxylabs).

## Docs

- [`AGENTS.md`](./AGENTS.md) — roles, architecture, 5-hour plan  
- [`PRD.md`](./PRD.md) — product requirements  
- [`DaddyFix/BRIAN_SETUP.md`](./DaddyFix/BRIAN_SETUP.md) — **Brian (AR) local setup**
- [`docs/README.md`](./docs/README.md) — backend API, architecture, deployment,
  sponsor integrations, and team handoff

## Backend quick start

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/docs` for generated OpenAPI documentation. The
paste-ready Swift integration contract is in
[`docs/backend-api.md`](./docs/backend-api.md).

## iOS app

```bash
open DaddyFix/DaddyFix.xcodeproj
```

Requires **Xcode 16+**, **iOS 18+**, and a **LiDAR iPhone** for the hero demo (simulator has no LiDAR).

### Team ownership

| Person | Platform | Area |
|--------|----------|------|
| **Brian** | Mac | `DaddyFix/DaddyFix/AR/*` (LiDAR + RealityKit) |
| **Kenji** | Mac | SwiftUI shell, voice, x402, `AppState`, iOS `VisionService` client |
| **Lucian** | Windows | Backend / agent / Daytona + Nosana + Oxylabs, shared JSON contract |

See [`AGENTS.md`](./AGENTS.md) for the full file ownership map.
