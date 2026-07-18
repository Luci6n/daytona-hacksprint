# Where to Continue — Lucian & Kenji
**Updated**: after merge of Brian’s vision/cloud/docs work to `main`  
**Branch**: work is on `main` (merged from `feature/kenji-vision`)

Full detail: `PRD.md` v0.2 §11–§15 · `AGENTS.md` §0, §5.

---

## Lucian (Windows — Daytona / agent / stack)

### Your job
Own the **cloud**. iOS only talks to your **public Daytona HTTPS URL**.

### Start here
```text
backend/
  main.py           # FastAPI: /health, /analyze, /analyze/mock
  daddy_agent.py    # pipeline hooks
  vision.py         # Kimi (Moonshot) + mock fallback
  models.py         # AnalysisResult = iOS contract
  oxylabs_client.py # stub → real scrape
  nosana_client.py  # stub → GPU path
  .env.example      # copy secrets into Daytona env (never commit .env)
```

### Do next (order)
1. **Deploy `backend/` on Daytona** → get public URL  
2. Set sandbox env: `MOONSHOT_API_KEY`, `KIMI_MODEL=kimi-k2.7-code`, Oxylabs, Nosana  
3. Prove: `GET /health`, `GET /analyze/mock`, `POST /analyze` with a real image  
4. **Add** `POST /analyze/stream/event` for Brian’s live demo  
   - Body idea: `{ sessionId, seq, imageBase64, mimeType, hint? }`  
   - Response: same `AnalysisResult` camelCase JSON  
5. Paste **public base URL** in team chat so Brian can set `APIConfig.baseURL`  
6. Oxylabs parts for Rinnai/ELCB if keys work; Nosana optional but show in `/health`

### Do **not**
- Edit Xcode / `AR/*`  
- Put API keys in the iOS app  

### Success when
Brian’s 17 Pro hits your URL and gets real (or solid mock) annotations.

---

## Kenji (Mac — UI / voice / pay; Xcode may be broken)

### Your job
**Product chrome** on top of Brian’s AR + VisionService. If Xcode fails, write Swift files / specs; **Brian merges and runs on device**.

### Start here (create / own these)
```text
DaddyFix/DaddyFix/
  Services/VoiceManager.swift      ← you
  Views/RepairGuideView.swift      ← you
  Views/PaymentModal.swift         ← you
  Services/x402Service.swift       ← you
  AppState.swift                   ← extend with Brian (phases, speak on analysis)
  Views/ContentView.swift          ← polish chrome (Brian has temporary shell)
```

### Already exists for you to call
- `VisionService` — `analyze` / `fetchServerMock` / `mockAnalyze`  
- `AppState.apply(result)` — places AR via Brian’s raycast  
- `raycastManager.onAnnotationSelected` — tap ELCB → open your guide/pay  
- Contract: `Models/AnalysisResult.swift`

### Do next (order)
1. **VoiceManager** — `AVSpeechSynthesizer`, speak `repairSteps[0]` + safety  
2. **RepairGuideView** — list steps + safety notes  
3. Wire: on analysis success → voice; on tap label → guide sheet  
4. **PaymentModal + x402** (P1 — can simulate 402 success)  
5. **Demo script** in README (judges): one-shot heater + mention live when ready  
6. Push a PR or send files; ask Brian to **⌘R on 17 Pro**

### Do **not**
- Rewrite `AR/*` without Brian  
- Block on Daytona — use **Local mock** button until Lucian’s URL exists  

### Success when
After Analyze, calm Daddy voice + steps UI; tap ELCB opens guide/buy.

---

## Brian (context for you two)

| Done | Next |
|------|------|
| LiDAR AR on device | LiveAnalysisSession (frame events) |
| VisionService + AppState shell | Point API at Lucian’s Daytona URL |
| Backend scaffold in repo | Pair stream API with Lucian |
| PRD/AGENTS status | Device-QA your PRs |

---

## Shared contract (don’t break)

```json
{
  "detectedItem": "string",
  "confidence": 0.9,
  "issues": ["..."],
  "arAnnotations": [
    { "type": "highlight", "x": 0.42, "y": 0.58, "z": null,
      "width": 0.18, "height": 0.12, "label": "ELCB", "color": "#22C55E" }
  ],
  "repairSteps": [
    { "step": 1, "instruction": "...", "safetyNote": "..." }
  ],
  "buyableParts": [
    { "id": "...", "name": "...", "estimatedPrice": "...", "x402Ready": true }
  ]
}
```

Live later adds: `sessionId`, `seq`, `eventType`.

---

## Integration order

```text
1. Lucian: Daytona URL live
2. Brian: one-shot Analyze on phone
3. Brian + Lucian: live stream events
4. Kenji: voice + guide + x402
5. Judges: Demo A (heater) then Demo B (live)
```

Ping in chat when your piece is ready so the next person isn’t blocked.
