# What Lucian’s backend still lacks (Brian view)

After merge of `feature/lucian-backend` into `main`. This is for Lucian/Kenji prioritization — **not** a request for Brian to rewrite Python.

## Strong already

| Area | Notes |
|------|--------|
| Package layout | `api/` / `domain/` / `integrations/` / tests |
| `POST /analyze` | `symptom`, `deviceHint`, `imageBase64` + camelCase out |
| `POST /speech/synthesize` | WAV path designed |
| Provider adapters | Oxylabs, Doubleword VL, Kimi/ai&, safety audit |
| `DEMO_MODE` | Deterministic Rinnai fixture |
| Live WS **code** | `WS /live/{sessionId}` frame / utterance / interrupt |
| Docs | `docs/backend-api.md` etc. |
| Fail loud | No silent mock on live provider failure |

## Gaps / blockers for a full judge demo

| Gap | Impact | Owner |
|-----|--------|--------|
| **Python version** | Tests fail on 3.9 (`str \| None` needs **3.10+**) | Lucian docs / Daytona image |
| **No persistent public Daytona URL** | Phone cannot reach agent on real network | Lucian + Kenji ops |
| **Live WS may not be fully proven** | Continuous 1–2s story incomplete if tests still red | Lucian |
| **Nosana TTS not deployed/warmed** | No real Daddy WAV; iOS falls back to AVSpeech | Lucian + Kenji |
| **Provider keys not verified e2e** | Live analyze may 500 without DEMO_MODE | Lucian |
| **No RTSP ingest in Lucian tree** | CCTV RTSP story missing; phone JPEG loop covers temporal | Lucian optional |
| **In-memory live sessions only** | Restart drops session; fine for hackathon | OK / later |
| **Safety requires “licensed” in every step** | Custom model output may hard-fail | Lucian prompt tuning |
| **Apple Speech not on backend** | Correct — iOS must send `symptom` text | Brian |

## Not lacking (iOS responsibility)

- AR capture, LiDAR place, barge-in audio stop, 1 fps client → **Brian**
- Public URL in `APIConfig` → **Brian** once Lucian pastes it

## Suggested Lucian order

1. Public URL + `DEMO_MODE=true` for reliable booth  
2. Prove live `/analyze` with keys when ready  
3. Finish/green live WS tests  
4. Nosana TTS real WAV  
5. Optional RTSP later  

## Brian client status (this push)

- Aligned `VisionService` to Lucian `POST /analyze`  
- AR frame snapshot on Scan  
- `VoiceManager` → `/speech/synthesize` + AVSpeech fallback  
- Explicit **Local mock** only (no silent live fallback)  
- Live WS client **not** built yet — next after URL + WS stable  
