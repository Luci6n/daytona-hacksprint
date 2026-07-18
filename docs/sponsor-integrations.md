# Sponsor integrations

DaddyFix uses each sponsor for a distinct production-shaped responsibility.
Provider readiness in `GET /health` means configuration is present; it is not a
live availability check.

| Sponsor | DaddyFix responsibility | Configuration | Code |
| --- | --- | --- | --- |
| Daytona | Isolated FastAPI/agent runtime and public signed preview URL | `DAYTONA_API_KEY`, `DAYTONA_API_URL`, `DAYTONA_TARGET` | `backend/daytona_sandbox.py` |
| Kimi / Moonshot | Multimodal repair reasoning when using the direct K2.6 path | `MOONSHOT_API_KEY`, `KIMI_BASE_URL`, `KIMI_MODEL` | `backend/integrations/kimi.py` |
| Nosana | GPU hosting for Qwen3-TTS VoiceDesign; GPU market discovery | `NOSANA_API_KEY`, `NOSANA_TTS_URL` | `backend/integrations/nosana.py`, `backend/speech_service/` |
| Oxylabs | Current manuals, troubleshooting context, and part/product search through Residential Proxy or Web Scraper API | `OXYLABS_USERNAME`, `OXYLABS_PASSWORD`, `OXYLABS_MODE` | `backend/integrations/oxylabs.py` |
| Doubleword | Qwen3-VL image observation for the ai& path and final safety audit | `DOUBLEWORD_API_KEY`, base URL, model | `backend/integrations/doubleword.py` |
| ai& | Japan-hosted Qwen reasoning and data-residency path | `AIAND_API_KEY`, `AIAND_BASE_URL`, `AIAND_MODEL` | `backend/integrations/kimi.py` |

## Daytona

Daytona is the control/runtime layer, not the GPU speech host. The helper creates
sandboxes through the Python SDK, starts Uvicorn in a persistent session, and
uses a signed preview URL for iOS access. The Daytona API key stays on Lucian's
machine and is deliberately excluded from sandbox environment forwarding.

Official references:
[Python SDK](https://www.daytona.io/docs/en/python-sdk/),
[preview URLs](https://www.daytona.io/docs/en/preview/).

## Kimi and ai&

`KimiReasoningClient` supports two OpenAI-compatible configurations:

- Complete ai& settings take priority and use the live-verified
  `qwen/qwen3.6-27b` model for text reasoning. Doubleword first converts the
  image into a structured visual observation.
- Otherwise, a Moonshot key uses `kimi-k2.6` with the image directly.

Do not place an ai& key in `MOONSHOT_API_KEY`; keys are scoped to their own base
URL. If neither configuration is complete, live analysis returns `503`.

## Nosana and Qwen3-TTS

Nosana runs the separate CUDA speech container. Qwen3-TTS VoiceDesign was chosen
because it can generate a controlled character voice from a natural-language
description rather than requiring a real person's voice sample. The configured
persona is a smooth, mature, reassuring, lightly flirtatious handyman voice;
safety instructions remain clear and non-comedic.

The official Qwen3-TTS project documents free-form voice design and recommends
a Python 3.12 environment:
[Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS).

Apple Speech remains the primary ASR because capture and partial transcription
belong on the iPhone. A Nosana Whisper service can be added later as an ASR
fallback without changing the `/analyze` contract.

## Oxylabs

The current integration uses the Web Scraper Realtime API with
username/password authentication and the Google Search source. Oxylabs AI
Studio is not required for this path; `OXYLABS_AI_STUDIO_API_KEY` can stay empty.
The returned context is capped before being added to the reasoning prompt.

## Doubleword

Use an inference key, not a platform-management key. The default vision model is
`Qwen/Qwen3-VL-30B-A3B-Instruct-FP8`. It has two jobs:

1. produce visible issues and normalized AR annotations for ai& reasoning;
2. reject unsafe final steps involving gas, energized electrical work, bypassed
   safety equipment, missing warnings, or unjustified certainty.

## Failure policy

- Configuration missing: `503`.
- Provider/network/invalid-response failure: `502`.
- Safety rejection: `502` with the concern; no unsafe result is returned.
- Invalid request or missing required live image: `422`.
- Demo fixtures are returned only when `DEMO_MODE=true`, never as a hidden live
  fallback.

This explicit failure behavior keeps the hero demo reliable without presenting
fabricated repair guidance as real provider output.
