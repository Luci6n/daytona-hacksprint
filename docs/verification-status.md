# Verify the DaddyFix deployment

This page records the live checks completed on July 19, 2026. It separates the proven local sponsor workflow from the public Daytona demo endpoint and the physical iPhone checks that still require the iOS team.

## Current verification status

| Surface | Status | Evidence |
| --- | --- | --- |
| Backend tests | Passed | 20 tests, Ruff, and mypy passed |
| Full live WebSocket workflow | Passed locally | `ready` → frame accepted → analysis → synthesis → audio metadata → binary WAV in 75.24s |
| Oxylabs | Passed | Web Scraper API returned bounded, valid repair context |
| Doubleword | Passed | Qwen3-VL returned structured visual observations and approved the final safety audit |
| ai& | Passed | `qwen/qwen3.6-27b` returned a schema-valid `AnalysisResult` |
| Nosana | Passed | One RTX 3090 job, model loaded, direct synthesis returned valid `audio/wav` with RIFF/WAVE headers |
| Daytona public API | Passed in demo mode | `/health` and `/openapi.json` returned 200; `/live/redeploy-smoke` returned `ready` |
| Daytona live sponsor mode | Blocked by platform egress | Fresh and existing sandboxes reset outbound TLS connections, including a control request to `example.com` |
| Physical iPhone workflow | Pending iOS team | Camera capture, Apple Speech, audio playback, and barge-in require an iPhone and the Swift client |

## Full local workflow evidence

The final probe used `DEMO_MODE=false` and the production WebSocket contract. It sent the official Rinnai image and one spoken symptom through the actual FastAPI application.

The response contained:

- `detectedItem`: Rinnai SENSEI RX tankless water heater
- `riskLevel`: `low`
- four repair steps with non-empty safety notes
- audio metadata followed by 1,178,924 bytes
- valid `RIFF` and `WAVE` headers

No provider returned a demo fixture or silent fallback.

## Public frontend handoff

The current Daytona sandbox runs commit `1c97e924331d4c309121a39d69f967dfceb180b6` in explicit demo mode. It contains no sponsor or control-plane credentials.

Share `.daytona/FRONTEND_HANDOFF.txt` privately with Kenji and Brian. The ignored file contains the signed base URL, REST endpoints, WebSocket URL construction, expiry, and a smoke command. Do not copy the Daytona API key into the iOS app.

## Remaining iPhone checks

Kenji or Brian must verify these steps on device:

1. Stream sampled camera frames over one WebSocket connection.
2. Send the final Apple Speech transcript as an `utterance` event.
3. Render the returned normalized AR annotations.
4. Play the returned WAV and stop playback immediately on barge-in.
5. Reject late events whose `turnId` no longer matches the active turn.

All configured sponsor credentials authenticated during this verification run. A future `401` or `403` response indicates that the affected key must be renewed.
