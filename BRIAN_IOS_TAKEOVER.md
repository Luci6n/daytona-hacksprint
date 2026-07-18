# Brian — Full iOS / Xcode Takeover

Kenji cannot use Xcode. **You own all shippable iOS work** for the demo.

## You own (everything on device)

| Area | Files / work |
|------|----------------|
| AR / LiDAR | `AR/*` (already yours) |
| Vision client | `Services/VisionService.swift` — match Lucian `POST /analyze` (`symptom`, `deviceHint`, `imageBase64`) |
| Voice | `VoiceManager` — `POST /speech/synthesize` → play WAV; AVSpeech fallback |
| UI shell | `ContentView`, `AppState`, `RepairGuideView`, `PaymentModal` |
| Payments | `x402Service` (simulate OK) |
| Speech in | Apple Speech → `symptom` |
| Device QA | Only machine that runs on **iPhone 17 Pro** |
| Live client later | 1 fps frames + WS when Lucian ready; barge-in audio stop |

## Integration loop you implement

```text
Frame JPEG + symptom (+ deviceHint)
  → POST /analyze  (Lucian Daytona/LAN)
  → placeAnnotations(result.arAnnotations)
  → POST /speech/synthesize → play WAV
  → tap ELCB → guide / buy UI
```

## Lucian gives you

- Public base URL (Kenji may help deploy)
- OpenAPI / `docs/backend-api.md`
- Stable `AnalysisResult` JSON
- TTS WAV endpoint

## Kenji gives you

- Deploy URL + smoke log
- Demo script / judge talk track
- Contract change alerts  
**Not** Swift PRs (unless pure text you paste yourself)

## Priority order

1. **P0** Align VisionService to Lucian analyze body  
2. **P0** One-shot on device with mock if URL missing  
3. **P0** WAV (or AVSpeech) after analysis  
4. **P0** Repair guide + tap selection  
5. **P1** x402 modal  
6. **P1** Live WS client when Lucian unblocks  

## Do not

- Put sponsor keys in the app  
- Wait on Kenji for code  
- Block on live WS for Demo A (REST first)  
