# Deploy from our end — which keys do you need?

**Never paste real keys into chat/Slack/Git.** Put them only in `.env` / `.env.local` (gitignored).

## Three deploy levels

| Level | What you get | Keys required |
|-------|----------------|---------------|
| **A. Local DEMO** | Phone on same Wi‑Fi can Scan + Live against Mac | **None** — only `DEMO_MODE=true` |
| **B. Local LIVE** | Real vision/reasoning on Mac | See “Live profiles” below |
| **C. Daytona public** | iPhone uses HTTPS/WSS URL anywhere | Level B keys **plus** `DAYTONA_API_KEY` |

---

## Keys by sponsor (names only)

| Env var | Sponsor | Needed for | Who usually has it |
|---------|---------|------------|--------------------|
| `DAYTONA_API_KEY` | Daytona | Create sandbox + public preview URL | Lucian / ops |
| `MOONSHOT_API_KEY` | Moonshot/Kimi | Live multimodal analyze (path A) | Team AI key |
| `AIAND_API_KEY` + `AIAND_BASE_URL` + `AIAND_MODEL` | ai& | Live text reasoning (path B) | Japan ai& console |
| `DOUBLEWORD_API_KEY` | Doubleword | Vision observe + safety (path B / audit) | Doubleword inference key |
| `OXYLABS_USERNAME` + `OXYLABS_PASSWORD` | Oxylabs | Manuals / product context when live | Oxylabs account |
| `NOSANA_TTS_URL` | Nosana | Real Daddy WAV from `/speech/synthesize` | After TTS container deploy |
| `NOSANA_API_KEY` | Nosana | Deploy/manage TTS job (operator only) | Lucian/ops |
| `NOSANA_TTS_BEARER_TOKEN` | Nosana | Only if TTS endpoint requires auth | Optional |

iOS app needs **zero** of these — only the public base URL.

---

## Recommended profiles

### 1) Demo booth (safest) — **start here**

```env
DEMO_MODE=true
```

No other keys. `/analyze` returns the Rinnai/ELCB fixture.  
Good for: LiDAR pins, Scan, Live wiring, judge reliability.

### 2) Live Moonshot path

```env
DEMO_MODE=false
MOONSHOT_API_KEY=sk-...
KIMI_BASE_URL=https://api.moonshot.ai/v1
KIMI_MODEL=kimi-k2.6
OXYLABS_USERNAME=...
OXYLABS_PASSWORD=...
# optional safety:
DOUBLEWORD_API_KEY=...
```

### 3) Live ai& path (your “moonshotai/kimi-k2.7-code” style)

```env
DEMO_MODE=false
AIAND_API_KEY=...
AIAND_BASE_URL=https://...   # exact URL from ai& console
AIAND_MODEL=moonshotai/kimi-k2.7-code
DOUBLEWORD_API_KEY=...       # required for image observation
OXYLABS_USERNAME=...
OXYLABS_PASSWORD=...
```

Do **not** put the ai& key into `MOONSHOT_API_KEY`.

### 4) Daddy voice

```env
NOSANA_TTS_URL=https://your-tts-endpoint
# NOSANA_TTS_BEARER_TOKEN=... if required
```

Without this, iOS falls back to **AVSpeech**.

### 5) Public Daytona

On **your Mac** (not inside iOS):

```env
DAYTONA_API_KEY=dtn_...
DEMO_MODE=true   # or false + live keys above
# plus any provider keys you want forwarded into the sandbox
```

---

## What to send **me** (the agent) if you want hands-on deploy help

**Do not send raw secrets in chat if you can avoid it.** Prefer:

1. “I have keys for: Moonshot / ai& / Oxylabs / Daytona / Nosana TTS” (checklist yes/no)  
2. Or put keys in `.env.local` yourself and ask me to **run deploy commands** that only read env files  

If you must share for setup: rotate the key after the hackathon.

Minimum to deploy **public DEMO** for the phone:

| Need | Required? |
|------|-----------|
| `DAYTONA_API_KEY` | **Yes** for public URL |
| `DEMO_MODE=true` | **Yes** for safe booth |
| Moonshot / ai& / Oxylabs | No for demo fixture |
| Nosana TTS | No for first demo |

Minimum for **live** vision on public URL:

| Need | Required? |
|------|-----------|
| `DAYTONA_API_KEY` | Yes |
| `DEMO_MODE=false` | Yes |
| Moonshot **or** (ai& + Doubleword) | Yes |
| Oxylabs user/pass | Yes (live agent builds with Oxylabs client) |

---

## Deploy commands (our Mac)

### Local (phone on same Wi‑Fi)

```bash
cd /path/to/daytona-hacksprint
cp .env.example .env.local   # edit DEMO_MODE=true
python3.12 -m venv .venv312 && source .venv312/bin/activate
pip install -r backend/requirements-dev.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

- Health: `http://127.0.0.1:8000/health`  
- Phone: set `APIConfig` to `http://<YOUR_MAC_LAN_IP>:8000`

### Daytona public (after keys in `.env.local`)

```bash
pip install -r backend/requirements-daytona.txt
# Ensure repo is pushed; Daytona must clone it
python -m backend.daytona_sandbox deploy \
  --repo-url https://github.com/Luci6n/daytona-hacksprint.git \
  --branch main
```

Copy printed **preview URL** → Brian `APIConfig.baseURL`.  
WebSocket: `https` → `wss` + `/live/<sessionId>`.

---

## From **your** end right now (Brian)

You can deploy **without waiting for every sponsor key**:

1. `DEMO_MODE=true` on Mac → LAN URL → phone Scan/Live  
2. Ask Lucian/Kenji for `DAYTONA_API_KEY` if you don’t have it → public URL  
3. Add Moonshot **or** ai& stack only when you want non-fixture vision  

**I do not need keys in chat to write code.**  
**I need keys in local `.env.local` (or you type them) only if you want me to run `deploy` / smoke against live providers.**
