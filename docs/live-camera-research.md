# Live camera agent research and DaddyFix recommendation

**Researched:** 2026-07-18
**Scope:** Gemini Live, OpenAI Realtime, LiveKit Agents, Pipecat, and their
official example repositories.

## Decision

DaddyFix should keep ARKit's camera and LiDAR session running locally at the
normal device frame rate, while sending only sampled JPEG keyframes and text
turns to a stateful FastAPI WebSocket.

For the hackathon MVP:

- send at most one JPEG per second while the user is speaking;
- send no passive frames, or one every 3–5 seconds, while idle;
- always send a fresh high-resolution keyframe when a turn starts, the user
  taps an AR object, or the transcript refers to "this", "that", or "here";
- keep Apple Speech on-device and send partial/final transcript events, not raw
  microphone audio;
- stop TTS locally before waiting for the backend to acknowledge an interrupt;
- keep only the newest passive frame plus explicitly referenced keyframes in
  session state.

This gives the user the important Gemini-Live-like behavior—an open camera,
persistent visual context, follow-up questions, and barge-in—without pretending
that the reasoning model processes every camera frame.

## What "live camera" products actually do

There are two separate frame rates:

1. **Display/AR rate:** ARKit continues rendering and tracking locally at its
   normal real-time rate.
2. **AI sampling rate:** the app periodically encodes a still image for the
   model, normally around one frame per second or only at turn boundaries.

The persistent conversation makes these sparse images feel continuous. The
model sees a sequence of useful snapshots and remembers prior turns; it does
not need a conventional H.264 video stream for the interaction to feel live.

## Comparison

| System | Client transport | What reaches the model | Turn/interruption behavior | Lesson for DaddyFix |
| --- | --- | --- | --- | --- |
| Gemini Live API | Stateful WebSocket | 16 kHz PCM, text, and JPEG images at no more than 1 FPS | Server VAD cancels generation; client must stop and clear queued audio | Strong evidence for sampled frames plus persistent context |
| OpenAI Realtime | WebRTC for mobile/browser; WebSocket for server media | Realtime text/audio plus image input; the model page explicitly says video is unsupported | Realtime session events and client-side audio control | A framework can call sampled images "video input" even when the model receives images |
| LiveKit Agents | WebRTC room | Default sampler sends JPEG at 1 FPS while speaking and 0.3 FPS while silent | Stops speech on interruption and can distinguish false interruptions | Good production transport and turn-management reference, but extra infrastructure for this hackathon |
| Pipecat | Recommends WebRTC for client audio | Typed audio/text/image/control frames; Gemini adapter caps video at 1 FPS | User turn start clears pending bot audio/text by default | Excellent pipeline reference; too large a framework migration for the current MVP |

## Gemini Live API

Google documents the public Live API as a stateful WebSocket accepting raw
16-bit PCM audio at 16 kHz, text, and JPEG images at no more than one frame per
second. Output audio is raw PCM at 24 kHz. Google also documents barge-in: VAD
cancels the current generation and sends an interruption event, after which the
client must immediately discard buffered playback audio.

Without context compression, Google documents an approximate 15-minute limit
for audio-only sessions and a 2-minute limit for audio-plus-video sessions.
Session resumption and context compression are therefore part of a production
implementation, not optional polish.

The Gemini consumer app's help page confirms that a user can share their camera
and interrupt Gemini Live. Google does **not** publish the consumer app's private
transport or exact sampler, so it would be speculation to claim the app itself
uses the public API identically.

Sources:

- [Gemini Live API overview and technical specifications](https://ai.google.dev/gemini-api/docs/live-api)
- [Raw WebSocket example, including JPEG video messages](https://ai.google.dev/gemini-api/docs/live-api/get-started-websocket)
- [VAD and interruption behavior](https://ai.google.dev/gemini-api/docs/live-api/capabilities)
- [Buffering, latency, and session best practices](https://ai.google.dev/gemini-api/docs/live-api/best-practices)
- [Session resumption and context management](https://ai.google.dev/gemini-api/docs/live-api/session-management)
- [Gemini app camera sharing and Live help](https://support.google.com/gemini/answer/15274899)

## OpenAI Realtime

The current GPT-Realtime model accepts text, audio, and image input and produces
text/audio output. Its official model page explicitly lists video as unsupported.
OpenAI recommends WebRTC when a mobile/browser client captures or plays audio,
and WebSocket when a server already owns a raw media pipeline.

This is compatible with the same perceived-live pattern: a camera transport or
framework samples the video track and adds individual images to the realtime
conversation. It is not evidence that the model consumes a video codec stream.

Sources:

- [GPT-Realtime modalities and endpoints](https://developers.openai.com/api/docs/models/gpt-realtime)
- [Realtime transport selection](https://developers.openai.com/api/docs/guides/realtime)

## LiveKit Agents

LiveKit uses WebRTC between the client and agent. Its default
`VoiceActivityVideoSampler` captures approximately one frame per second while
the user is speaking and 0.3 FPS while silent. Frames are resized to fit
1024×1024 and JPEG encoded. Only the newest camera or screen-share track is
used.

LiveKit also shows a cheaper cascaded pattern: continuously retain only the
latest video frame, then attach that image to the next completed user turn.
Video is passive and does not trigger a turn by itself.

For interruptions, LiveKit stops agent speech when user speech is detected.
Its session history is truncated to the portion the user actually heard, and
its managed adaptive mode can distinguish a real barge-in from a backchannel
such as "uh-huh".

Official examples worth inspecting:

- [LiveKit Agents repository](https://github.com/livekit/agents) — links a full
  Gemini Live vision example with an iOS client.
- [Runnable Python agent examples](https://github.com/livekit-examples/python-agents-examples)
  — includes Gemini Live Vision and non-realtime camera-vision patterns.
- [Swift agent starter](https://github.com/livekit-examples/agent-starter-swift)
  — useful if the team later adopts WebRTC on iOS.

Sources:

- [LiveKit Agents architecture](https://docs.livekit.io/agents/)
- [Live video sampling and latest-frame pattern](https://docs.livekit.io/agents/multimodality/vision/video/)
- [Video sampler defaults](https://docs.livekit.io/agents/logic/sessions/)
- [Turn and interruption handling](https://docs.livekit.io/agents/logic/turns/)

## Pipecat

Pipecat treats audio, text, images, and control messages as typed frames moving
through a processor pipeline. It recommends WebRTC for user-facing client
audio because WebSockets over TCP do not provide media jitter handling, packet
loss behavior, or built-in echo cancellation. Its Gemini Live adapter throttles
video to a maximum of one frame per second.

Pipecat's default turn setup combines Silero VAD with a smart turn analyzer.
When a user turn starts, interruption is enabled by default: bot speech stops,
pending audio/text frames are cleared, and the pipeline becomes ready for the
new input.

Official examples worth inspecting:

- [Pipecat examples](https://github.com/pipecat-ai/pipecat-examples) — includes
  Gemini Live starters, peer-to-peer WebRTC, and WebSocket variants.
- [Pipecat framework](https://github.com/pipecat-ai/pipecat) — source for its
  media-frame and interruption pipeline.

Sources:

- [Pipecat transport comparison](https://docs.pipecat.ai/client/concepts/choosing-a-transport)
- [Speech input, VAD, smart turns, and interruptions](https://docs.pipecat.ai/pipecat/learn/speech-input)
- [Gemini Live adapter behavior](https://docs.pipecat.ai/api-reference/server/services/s2s/gemini-live)

## Why a WebSocket is still reasonable for this MVP

Pipecat and OpenAI are right that WebRTC is a better production transport for
raw, bidirectional client audio. DaddyFix's first live protocol does not send
raw audio: Apple Speech owns microphone capture, and the WebSocket carries JSON
transcripts, sampled JPEGs, control events, and short WAV responses. That makes
a FastAPI WebSocket an acceptable hackathon shortcut.

Move to WebRTC/LiveKit/Pipecat only if the product later needs continuous raw
audio, server-side ASR, media jitter handling, automatic network recovery, or
true streaming speech-to-speech.

## Recommended DaddyFix flow

```text
ARKit camera + LiDAR (local 30/60 FPS)
        |
        +-- persistent AR rendering and world anchors
        |
        +-- sampled JPEG/keyframe -------------------------+
Apple Speech partial/final transcript --------------------+-- FastAPI /live WebSocket
                                                         |
                                                   latest-frame cache
                                                   turn + analysis history
                                                         |
                                       Oxylabs -> Doubleword -> ai& reasoning
                                                         |
                                              structured AnalysisResult
                                                         |
                                            Nosana Qwen3-TTS short WAV
                                                         |
                                             iOS playback + AR updates
```

### Frame policy

- **Speaking:** up to 1 FPS.
- **Idle:** 0 FPS for the simplest MVP; optionally 0.2–0.3 FPS.
- **Turn start:** capture one fresh keyframe immediately.
- **Tap/deictic reference:** capture a fresh high-resolution keyframe and attach
  tap coordinates and LiDAR/raycast depth.
- **Retention:** replace the passive frame in memory; retain only keyframes that
  a conversation turn references.

A future frame envelope should include `frameId`, capture timestamp,
orientation, normalized tap point, and optional raycast depth. The first MVP can
ship with `imageBase64` and `deviceHint`, then add metadata without changing the
shared `AnalysisResult` model.

### Barge-in must be local-first

1. Keep Apple Speech listening while TTS plays.
2. Configure iOS voice processing/echo cancellation so the Daddy voice does not
   repeatedly trigger its own ASR.
3. On credible user partial speech, immediately stop the player and clear its
   queued audio locally.
4. Increment `turnId`/`generationId` and send an `interrupt` event.
5. The backend cancels the current analysis/TTS task where possible.
6. iOS discards all late analysis or audio carrying the old turn ID.
7. The next utterance uses the newest keyframe and prior completed analysis.

Client-side stopping cannot wait for a network round trip; otherwise the agent
will continue talking over the user. Also, cancelling an asyncio task does not
necessarily terminate a synchronous HTTP/GPU request already running in a
worker thread. Turn IDs are therefore required to reject late results.

Apple's voice-processing APIs are the relevant iOS primitive:
[AVAudioEngine voice processing](https://developer.apple.com/documentation/avfaudio/avaudioengine/setvoiceprocessingenabled(_:)).

### TTS latency constraint

The current Nosana speech service returns a complete WAV. That is interruptible
locally but not genuinely streaming. For the MVP, synthesize one short sentence
or clause per response so playback can start earlier. A production version
should make the Nosana service emit audio chunks over WebSocket/WebRTC and tag
each chunk with its generation ID.

## What not to build during the hackathon

- Do not upload 30 FPS video to the LLM.
- Do not append every sampled image permanently to prompt history.
- Do not move LiDAR tracking or RealityKit anchoring to the backend.
- Do not add LiveKit or Pipecat solely for sponsor count.
- Do not claim whole-WAV TTS is streaming.
- Do not claim the Gemini consumer app's private implementation is documented.

## Upgrade path after the demo

1. Add richer frame metadata and explicit keyframe references.
2. Segment or stream Nosana TTS with generation IDs.
3. Add a semantic interruption filter so acknowledgements like "mm-hm" do not
   always cancel the response.
4. Persist resumable session state outside a single backend process.
5. Adopt WebRTC through LiveKit or Pipecat only when continuous media transport
   becomes a real requirement.
