# DaddyFix documentation

Use this directory for implementation and handoff details. `AGENTS.md` remains
the source of truth for ownership, while `PRD.md` remains the source of truth
for product scope.

| Document | Audience | Purpose |
| --- | --- | --- |
| [`backend-api.md`](backend-api.md) | Kenji, backend consumers | Paste-ready `/analyze` and TTS contract, samples, Swift sketch, errors. |
| [`backend-architecture.md`](backend-architecture.md) | Backend contributors | Layer boundaries, provider ports, request sequences, extension rules. |
| [`live-camera-research.md`](live-camera-research.md) | Whole team | Primary-source comparison of Gemini Live, OpenAI Realtime, LiveKit, and Pipecat, plus the recommended camera and interruption design. |
| [`deployment.md`](deployment.md) | Lucian, demo operator | Local startup, Daytona API deployment, Nosana TTS deployment, cleanup. |
| [`daytona-outbound-network.md`](daytona-outbound-network.md) | Backend contributors, demo operator | Daytona TLS-reset diagnosis, least-privilege provider allowlist, validation, and escalation steps. |
| [`sponsor-integrations.md`](sponsor-integrations.md) | Team, judges | Exact role of every sponsor, configuration, and failure behavior. |
| [`team-handoff.md`](team-handoff.md) | Kenji and Brian | Shared-model status, VisionService checklist, AR coordinate semantics. |
| [`verification-status.md`](verification-status.md) | Team, demo operator | Live evidence, public-demo limits, and remaining iPhone checks. |

FastAPI also serves generated OpenAPI documentation at `/docs` and
`/openapi.json` while the backend is running.
