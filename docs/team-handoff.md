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
| `riskLevel` | `risk_level` alias | Not added yet | Brian must mirror before displaying risk |
| `issues` | `issues` | `issues` | Matched |
| `arAnnotations` | `ar_annotations` alias | `arAnnotations` | Matched |
| `repairSteps` | `repair_steps` alias | `repairSteps` | Matched |
| `buyableParts` | `buyable_parts` alias | `buyableParts` | Matched |

Nested annotation and buyable-part fields are matched. Python now requires a
nonempty `safetyNote`; Swift still accepts it as optional, which remains decode
compatible but should be tightened by Brian. The Python API test verifies the
same Rinnai/ELCB fixture values stored in Swift plus the new `riskLevel`.

Brian should add the following required field to `AnalysisResult.swift` before
rendering live risk state:

```swift
let riskLevel: String // "low", "medium", "high", "emergency"
```

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

- Store the selected Daytona/local base URL in one configuration point.
- Check `/health` before enabling live analysis.
- JPEG-resize the captured frame, then encode it as a data URL.
- Send the Apple Speech transcript in `symptom`.
- Use a 120-second request timeout for hackathon cold starts.
- Check HTTP status before decoding `AnalysisResult`.
- Decode non-2xx bodies as `{ "detail": String }` and show the real error.
- Decode and visibly display `riskLevel`; treat `emergency` as a stop condition.
- Do not implement a silent local/demo fallback for live server errors.
- Preserve the captured image's aspect/crop metadata for AR coordinate mapping.

The complete paste-ready request, response, Swift sketch, and error table are in
[`backend-api.md`](backend-api.md).

### Voice checklist

- Use Apple Speech/`SFSpeechRecognizer` for microphone transcription.
- Confirm `supportsOnDeviceRecognition` at runtime; Apple support varies by
  language/device.
- Send the final transcript to `/analyze`, not raw audio.
- Send a chosen repair instruction to `/speech/synthesize`.
- Treat the response as WAV `Data` and play it with `AVAudioPlayer`.
- Fall back to `AVSpeechSynthesizer` only as an explicit degraded mode if the
  Nosana service is unavailable.

### Live camera and interruption checklist

- Keep ARKit rendering locally; send sampled JPEGs, not a 30 FPS video stream.
- Open one `WS /live/{sessionId}` connection and wait for `ready`.
- Send up to 1 FPS while speaking and a fresh keyframe before each utterance.
- Use Apple Speech partial text only to detect barge-in; send final text as the
  `utterance` event.
- Track the server-issued `turnId` for analysis and audio.
- On barge-in, stop and flush audio locally first, then send `interrupt`.
- Ignore late messages whose `turnId` is no longer current.
- Enable voice processing/echo cancellation while listening during TTS.
- Expect complete binary WAV after the `audio` metadata event; streaming chunks
  are not implemented yet.

The complete event contract is in [`backend-api.md`](backend-api.md#ws-livesessionid),
and the design evidence is in
[`live-camera-research.md`](live-camera-research.md).

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
