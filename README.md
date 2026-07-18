# DaddyFix — Daytona Hacksprint

Spatial AR home repair on **iPhone 17 Pro LiDAR** + cloud **Daddy Agent** on **Daytona** (Kimi + Oxylabs + Nosana).

## Docs

| Doc | Purpose |
|-----|---------|
| [`PRD.md`](./PRD.md) | Product, **status board**, live-stream design, **task split** |
| [`AGENTS.md`](./AGENTS.md) | Roles, architecture, ownership, checklists |
| [`DaddyFix/BRIAN_SETUP.md`](./DaddyFix/BRIAN_SETUP.md) | Brian on-device Xcode |
| [`DaddyFix/LUCIAN_INTEGRATION.md`](./DaddyFix/LUCIAN_INTEGRATION.md) | AR embed notes (iOS) |
| [`backend/README.md`](./backend/README.md) | FastAPI local / Daytona |

## How far are we? (summary)

| Slice | ~Ready | Who unblocks |
|-------|--------|--------------|
| LiDAR AR on 17 Pro | **High** | Brian polish |
| One-shot cloud analyze | **Medium** | Lucian Daytona URL + Kimi |
| **Live stream events** | **Low** | Brian client + Lucian API |
| Voice / pay UI | **Low** | Kenji (+ Brian device QA) |

See **PRD §15** for detail.

## Architecture (one line)

Phone sends **frames/events** → **Daytona agent** reasons → phone **LiDAR-locks** annotations. Keys stay in the cloud.

## Team

| Person | Focus |
|--------|--------|
| **Brian** | AR + live capture + device ship |
| **Lucian** | Daytona + agent + Oxylabs/Nosana/Kimi |
| **Kenji** | Voice, guide UI, x402, demo script |

## iOS

```bash
open DaddyFix/DaddyFix.xcodeproj
```

Real **LiDAR iPhone** required for the hero demo.
