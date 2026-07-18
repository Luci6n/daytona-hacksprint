# DaddyFix Backend (FastAPI + Kimi vision)

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Status + model flags + `ffmpeg` / RTSP readiness |
| GET | `/analyze/mock` | Perfect water-heater `AnalysisResult` (no LLM) |
| POST | `/analyze` | One-shot JSON `{ "imageBase64", "mimeType?", "hint?" }` |
| POST | `/analyze/upload` | Multipart image file |
| POST | `/stream/rtsp/start` | **Continuous**: sample RTSP camera every N sec → agent |
| POST | `/stream/phone/start` | Open phone-driven live session |
| POST | `/stream/phone/event` | iOS posts one live JPEG event |
| GET | `/stream/{sessionId}/latest` | Latest `AnalysisResult` for AR refresh |
| GET | `/stream/{sessionId}/status` | seq / errors / active |
| POST | `/stream/{sessionId}/stop` | Stop RTSP loop |

Response shape matches iOS `AnalysisResult` (camelCase).

### Why RTSP (not only screenshots)

A single still cannot show *change over time* (water dripping, flow starting).  
RTSP is the standard control/media path for IP cameras (often port **554**).  
Daytona **pulls** frames from the stream on an interval → Kimi reasons → JSON.  
iPhone LiDAR still **places** AR pins (poll `/latest` or use phone events).

```bash
# Start continuous RTSP analysis
curl -s -X POST http://127.0.0.1:8000/stream/rtsp/start \
  -H 'Content-Type: application/json' \
  -d '{"rtspUrl":"rtsp://user:pass@cam:554/stream1","intervalSec":2,"hint":"leaking pipe"}'

# Poll results for AR
curl -s http://127.0.0.1:8000/stream/<sessionId>/latest | jq
```

Install ffmpeg in Daytona: `apt-get update && apt-get install -y ffmpeg`

## Local run

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# .env already has keys locally; or: cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000
```

Test:

```bash
curl -s http://127.0.0.1:8000/health | jq
curl -s http://127.0.0.1:8000/analyze/mock | jq
```

## Kimi / Moonshot

- Base URL: `https://api.moonshot.ai/v1` (OpenAI-compatible)
- Env: `MOONSHOT_API_KEY`, `KIMI_MODEL` (default `kimi-k2.7-code`)
- Mode: `VISION_MODE=kimi` or `mock`

If the model id fails, try:
- `kimi-k2.7-code`
- `kimi-k2.5`
- `moonshotai/kimi-k2.7-code` (some gateways)

On any Kimi error, API **falls back to mock** so the demo still works.

## Daytona

Deploy this folder in a Daytona sandbox, expose port 8000, set iOS:

```text
APIConfig.baseURL = https://YOUR-DAYTONA-PUBLIC-URL
```

## Security

Never commit `.env`. Rotate keys if pasted in chat/Slack.
