# Backend contract and team handoff

## Ownership (current)

| Person | Owns |
|--------|------|
| **Lucian** | `backend/`, Python JSON contract, Daytona, providers, API docs |
| **Brian** | **All iOS/Xcode**: ARKit/LiDAR, `VisionService`, `VoiceManager`, SwiftUI, payments, live WS client, device QA |
| **Kenji** | Deploy/smoke/docs only — **no Swift, no Xcode** |

Do **not** assign Swift files to Kenji (Xcode unavailable; causes wrong ownership).

## `AnalysisResult` status

| JSON field | Python | Swift | Status |
| --- | --- | --- | --- |
| `detectedItem` | `detected_item` alias | `detectedItem` | Matched |
| `confidence` | `confidence` | `confidence` | Matched |
| `issues` | `issues` | `issues` | Matched |
| `arAnnotations` | `ar_annotations` alias | `arAnnotations` | Matched |
| `repairSteps` | `repair_steps` alias | `repairSteps` | Matched |
| `buyableParts` | `buyable_parts` alias | `buyableParts` | Matched |

Any field change: Lucian + Brian agree in chat; update both sides.

## Brian — `VisionService` + voice + live (iOS)

- `APIConfig.baseURL` → Daytona or LAN IP (not secrets).
- `GET /health` before demo.
- JPEG resize ~1280, data URL in `imageBase64`.
- `POST /analyze` with `symptom`, `deviceHint`, `imageBase64`.
- 120s timeout; surface `{ "detail" }` errors — **no silent mock** on live fail.
- `POST /speech/synthesize` → WAV; AVSpeech only as explicit fallback.
- Live: `WS /live/{sessionId}`, frames every 1–2s, barge-in `interrupt`.
- Bundle ID: **`com.daddyfix.app`** (Personal Team: Brian Har).

See [`backend-api.md`](backend-api.md).

## Brian — AR annotation checklist

- `x`/`y` normalized 0…1, top-left of **captured** image.
- Correct for aspectFill before raycast.
- Prefer LiDAR depth when `z` is null.
- World-space anchors so pins stay while walking.
- Support `highlight`, `arrow`, `text` for hero demo.

## Integration acceptance test

1. `/health` → `status: ok`.
2. Brian Scan (or demo mode analyze) with symptom “No hot water”.
3. Decode `AnalysisResult`; place ELCB at ~(0.42, 0.58).
4. TTS or AVSpeech for step 1 + safety.
5. Live mode: frames stream; errors are explicit if providers missing.
