# Where to Continue — Team Split (Xcode → Brian only)

**Updated**: Kenji has **no Xcode**. All iOS implementation = **Brian**.  
Kenji = **deploy / smoke / docs** without colliding with **Lucian** backend ownership.

| Doc | Audience |
|-----|----------|
| `BRIAN_IOS_TAKEOVER.md` | Brian — full iOS checklist |
| `KENJI_ASSIGNMENTS.md` | Kenji — ops only |
| Lucian progress paste + `docs/` on his branch | Lucian |

---

## Lucian (Windows — backend owner)

### Own
- Agent code, providers (Oxylabs, Doubleword, Kimi/ai&, Nosana TTS service code)
- `POST /analyze`, `POST /speech/synthesize`, future `WS /live/{sessionId}`
- Architecture; fix tests; safety validation
- Final say on backend design

### Do next
1. Land/push `feature/lucian-backend`  
2. Implement live WebSocket (make the 2 tests pass)  
3. Work with **Kenji** on persistent Daytona URL (he runs steps; you approve)  
4. Finish Nosana TTS image deploy path (Kenji can assist Docker/warmup)  
5. Paste public URL + any contract deltas to Brian  

### Do not
- Expect Kenji to write Swift  
- Expect Brian to implement Python providers  

---

## Kenji (no Xcode — ops lane)

### Own
See **`KENJI_ASSIGNMENTS.md`**.

| Do | Don’t |
|----|--------|
| Daytona persistent deploy **with Lucian** → public URL for Brian | Edit Lucian agent/provider code unasked |
| Smoke: `/health`, `/analyze`, `/speech/synthesize` → log | Commit secrets |
| Env checklist (names only) | Any Xcode / `.swift` |
| Judge one-pager + demo script | Redesign API without Lucian |
| Nosana TTS deploy assist if Lucian asks | Own production architecture |

### Success
Brian has a **public base URL** + you confirmed analyze + WAV smoke pass.

---

## Brian (all Xcode + 17 Pro)

### Own
See **`BRIAN_IOS_TAKEOVER.md`**.

- Entire iOS app: AR + analyze client + Speech + WAV voice + UI + x402  
- Match Lucian: `symptom` + `deviceHint` + `imageBase64` → `AnalysisResult`  
- `POST /speech/synthesize` → play WAV (AVSpeech fallback)  
- Device integration test for judges  

### Success
One-shot demo: frame → analyze → LiDAR pin → Daddy audio → tap guide/buy.

---

## Integration order

```text
1. Lucian: API solid on branch (+ Kenji smoke)
2. Kenji + Lucian: public Daytona URL
3. Brian: APIConfig URL → full device loop
4. Lucian: live WS → Brian client later
5. Kenji: demo script / judge stack story
```

## Collision rules

```text
Python agent / providers  → Lucian only
Deploy button-pushing     → Kenji OK if Lucian agrees
Swift / Xcode             → Brian only
Secrets                   → never in git or iOS
```
