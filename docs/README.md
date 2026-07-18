# DaddyFix documentation

Use this directory for implementation and handoff details. `AGENTS.md` remains
the source of truth for ownership, while `PRD.md` remains the source of truth
for product scope.

| Document | Audience | Purpose |
| --- | --- | --- |
| [`backend-api.md`](backend-api.md) | Kenji, backend consumers | Paste-ready `/analyze` and TTS contract, samples, Swift sketch, errors. |
| [`backend-architecture.md`](backend-architecture.md) | Backend contributors | Layer boundaries, provider ports, request sequences, extension rules. |
| [`deployment.md`](deployment.md) | Lucian, demo operator | Local startup, Daytona API deployment, Nosana TTS deployment, cleanup. |
| [`sponsor-integrations.md`](sponsor-integrations.md) | Team, judges | Exact role of every sponsor, configuration, and failure behavior. |
| [`team-handoff.md`](team-handoff.md) | Kenji and Brian | Shared-model status, VisionService checklist, AR coordinate semantics. |

FastAPI also serves generated OpenAPI documentation at `/docs` and
`/openapi.json` while the backend is running.
