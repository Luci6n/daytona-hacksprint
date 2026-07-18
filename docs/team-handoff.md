# Backend contract and team handoff

## Ownership

`AGENTS.md` is authoritative:

- Lucian owns `backend/`, the Python-first JSON contract, API documentation,
  Daytona, Oxylabs, and Nosana integration.
- Kenji owns `VisionService.swift`, `VoiceManager.swift`, SwiftUI, payments, and
  the iOS integration wiring.
- Brian owns ARKit/LiDAR, raycasting, and RealityKit annotation placement.

Lucian documents the `VisionService` wire contract but does not edit Kenji's
Swift client implementation.

## `AnalysisResult` status

The checked-in definitions are aligned:

| JSON field | Python | Swift | Status |
| --- | --- | --- | --- |
| `detectedItem` | `detected_item` alias | `detectedItem` | Matched |
| `confidence` | `confidence` | `confidence` | Matched |
| `issues` | `issues` | `issues` | Matched |
| `arAnnotations` | `ar_annotations` alias | `arAnnotations` | Matched |
| `repairSteps` | `repair_steps` alias | `repairSteps` | Matched |
| `buyableParts` | `buyable_parts` alias | `buyableParts` | Matched |

Nested annotation, repair-step, and buyable-part fields are also matched. The
Python API test verifies the same Rinnai/ELCB fixture stored in Swift.

Any future field-name or optionality change must be proposed in team chat and
updated on both sides together.

## Kenji — `VisionService.swift` checklist

- Store the selected Daytona/local base URL in one configuration point.
- Check `/health` before enabling live analysis.
- JPEG-resize the captured frame, then encode it as a data URL.
- Send the Apple Speech transcript in `symptom`.
- Use a 120-second request timeout for hackathon cold starts.
- Check HTTP status before decoding `AnalysisResult`.
- Decode non-2xx bodies as `{ "detail": String }` and show the real error.
- Do not implement a silent local/demo fallback for live server errors.
- Preserve the captured image's aspect/crop metadata for AR coordinate mapping.

The complete paste-ready request, response, Swift sketch, and error table are in
[`backend-api.md`](backend-api.md).

## Kenji — voice checklist

- Use Apple Speech/`SFSpeechRecognizer` for microphone transcription.
- Confirm `supportsOnDeviceRecognition` at runtime; Apple support varies by
  language/device.
- Send the final transcript to `/analyze`, not raw audio.
- Send a chosen repair instruction to `/speech/synthesize`.
- Treat the response as WAV `Data` and play it with `AVAudioPlayer`.
- Fall back to `AVSpeechSynthesizer` only as an explicit degraded mode if the
  Nosana service is unavailable.

## Kenji — live camera and interruption checklist

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

- `x` and `y` are normalized to the captured image with top-left origin.
- Correct for `aspectFill` cropping before converting to a view point.
- Use the resulting screen point for an ARKit raycast.
- Prefer LiDAR/raycast depth when `z` is null.
- Anchor the RealityKit entity in world space so it stays fixed while walking.
- Support `highlight`, `arrow`, and `text` for the hero fixture first.

## Integration acceptance test

1. Backend `/health` returns `status: ok`.
2. Kenji sends `{ "symptom": "No hot water" }` in demo mode.
3. Swift decodes the returned `AnalysisResult` without custom key mapping.
4. Brian renders the ELCB highlight at `(0.42, 0.58)` and anchors it.
5. Kenji requests TTS for the first repair step and plays the WAV.
6. The safety note is visible and/or spoken.
7. Switching to live mode produces an explicit error if any provider is missing;
   it never pretends a provider call succeeded.
