# DaddyFix Backend (FastAPI + Kimi vision)

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Status + model flags |
| GET | `/analyze/mock` | Perfect water-heater `AnalysisResult` (no LLM) |
| POST | `/analyze` | JSON `{ "imageBase64", "mimeType?", "hint?" }` |
| POST | `/analyze/upload` | Multipart image file |

Response shape matches iOS `AnalysisResult` (camelCase).

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
