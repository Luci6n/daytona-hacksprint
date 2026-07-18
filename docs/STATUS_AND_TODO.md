# DaddyFix status — why things fail + what’s left

**Last update:** after Lucian ai& model fix + local live path investigation  
**Audience:** Brian (iOS) · Lucian (backend/Daytona) · Kenji (ops)

---

## TL;DR

| Question | Answer |
|----------|--------|
| Is Daytona “dead”? | **The sandbox process can be up**, but **live AI calls from inside Daytona fail** (no egress to ai&/Doubleword). Result: **Analysis incomplete**. |
| Are we doomed without Daytona? | **No for AR/LiDAR.** Yes for **sponsor story** if judges require a **public Daytona URL** — fix is **egress or DEMO_MODE on Daytona**, not abandon Daytona. |
| Does local work? | **Backend on Mac `127.0.0.1:8000` works** with real providers (mouse/battery path proven). **Phone often cannot reach Mac** if LAN IP is wrong/firewalled (e.g. `10.244.x` timed out). |
| Code status | Live/WS client + RTSP + Lucian-aligned ai& model (`qwen/qwen3.6-27b`) are in repo; need clean push + working **reachable** API URL on phone. |

---

## 1. Why Daytona looks dead

### What works on Daytona
- Sandbox starts, `uvicorn` runs  
- `GET /health` can return `ok`  
- Env shows keys present: `oxylabs/doubleword/aiand: true`  

### What fails
When `POST /analyze` runs **inside the sandbox**:

```text
Kimi request failed: Connection error.
Doubleword vision request failed: Connection error.
Oxylabs: Connection reset by peer
```

So the agent falls into **Analysis incomplete** (by design after we removed silent water-heater mock).

### Root cause
**Daytona sandbox cannot open outbound HTTPS to:**
- `https://api.aiand.com/v1`
- `https://api.doubleword.ai/v1`
- sometimes Oxylabs

This is **network policy / egress**, not “wrong iOS code” and not “API missing.”

### Lucian branch fix we grabbed
From `origin/feature/lucian-backend` (`bba342e` etc.):

| Item | Correct value |
|------|----------------|
| `AIAND_BASE_URL` | `https://api.aiand.com/v1` (docs + Lucian `.env.example`) |
| `AIAND_MODEL` | **`qwen/qwen3.6-27b`** (verified; **not** `moonshotai/kimi-k2.7-code`) |
| ai& call | `temperature=0`, `max_completion_tokens=1000`, `reasoning_effort: none` |
| Vision | Doubleword VL first; ai& is **text** reasoning |
| Oxylabs | `OXYLABS_MODE=web_scraper_api` (or residential_proxy) |

We merged those into our tree.

### How to un-doom Daytona (Lucian / ops)

1. **Allow egress** from Daytona sandboxes to ai& / Doubleword / Oxylabs, **or**  
2. Deploy with **`DEMO_MODE=true`** on Daytona for a **reliable public URL** (fixture, not live mouse), **or**  
3. Put a **proxy/relay** that has egress and that Daytona can call, **or**  
4. Confirm Daytona plan allows outbound HTTPS (some free/restricted sandboxes block it).

Sponsor story can still be: “Agent **runs on Daytona**; models are called when egress is open; DEMO_MODE for reliability.”

---

## 2. Why “local still not working” on the phone

| Path | Result |
|------|--------|
| Mac → `http://127.0.0.1:8000` | ✅ Works (health + analyze) |
| Mac → LAN IP (e.g. `10.244.57.152:8000`) | ❌ Timed out (bad interface / VPN / firewall) |
| Phone → same LAN IP | ❌ Will fail if Mac can’t even hit that IP |
| Phone → `127.0.0.1` | ❌ Always wrong (that’s the phone itself) |

**Proven on Mac (not phone):** live agent returned e.g.  
`Wireless Mouse` + labels `Empty Battery Compartment` / `Insert Batteries Here`.

So local **logic** works; **phone reachability** is the gap.

### Fix local phone path
1. Find a **real LAN IP** the phone can reach:  
   System Settings → Network → Wi‑Fi → IP (often `192.168.x.x`, not a `10.244` VPN).  
2. Run:  
   `uvicorn backend.main:app --host 0.0.0.0 --port 8000`  
3. Set `APIConfig.baseURL` to `http://THAT_IP:8000`  
4. Allow macOS firewall for Python  
5. Same Wi‑Fi, no client isolation  

---

## 3. What’s done vs not done

### Done ✅
- [x] iOS AR / LiDAR / place / tap / debug sphere  
- [x] iOS Scan → `POST /analyze` (Lucian body: symptom, deviceHint, imageBase64)  
- [x] iOS Live WS client (1–2s frames) + RTSP client hooks  
- [x] iOS VoiceManager (TTS URL + AVSpeech fallback)  
- [x] UI: RepairGuide, PaymentModal, AppState  
- [x] Lucian backend merge on main (structure)  
- [x] RTSP server routes + tests  
- [x] Real-scene prompts (mouse/battery, not only heater)  
- [x] Lucian-verified **ai& model** `qwen/qwen3.6-27b` + call params  
- [x] Oxylabs web_scraper mode support (from Lucian)  
- [x] Backend unit tests **19 passed** (Python 3.12)  
- [x] Local Mac live analyze proven for mouse/battery **text path**  

### Not done / blocked ❌
- [ ] **Daytona outbound** to ai&/Doubleword (live public URL with real vision)  
- [ ] **Phone successfully hitting** a reachable API (LAN or fixed Daytona)  
- [ ] End-to-end **on device**: real mouse photo → correct battery-bay highlight  
- [ ] Nosana TTS deployed + real Daddy WAV  
- [ ] Live WS fully proven on device (1–2s stream)  
- [ ] RTSP with real camera URL end-to-end  
- [ ] Apple Speech mic → symptom (typed field only for now)  
- [ ] Stable public URL for judges (non-expiring / re-deploy script)  

---

## 4. Recommended path for the next hour

### Path A — Public Daytona for judges (stack story)
1. Redeploy with **`DEMO_MODE=true`** → always returns solid ELCB fixture on public HTTPS.  
2. Tell judges: agent runs on Daytona; vision providers wired; live egress pending.  
3. Separately demo **LiDAR lock** + mock/local smart path if needed.

### Path B — Real mouse smartness (what you want)
1. Run API **on Mac** with working Wi‑Fi IP (`192.168…`).  
2. Phone `APIConfig` = that IP.  
3. Scan open mouse battery bay.  
4. Keep Daytona for later once Lucian fixes egress.

### Path C — Both
- Daytona = DEMO_MODE public URL for stack.  
- Mac LAN = live vision when demoing mouse.

---

## 5. Commands cheat sheet

```bash
# tests
.venv312/bin/python -m pytest backend/tests -q

# local API (use a Wi-Fi IP the phone can reach)
set -a && source .env.local && set +a
.venv312/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Daytona (needs DAYTONA_API_KEY in .env.local)
.venv312/bin/python -m backend.daytona_sandbox deploy \
  --repo-url https://github.com/Luci6n/daytona-hacksprint.git \
  --branch main
```

---

## 6. Message to Lucian

> Daytona sandbox is up but **outbound Connection error** to `api.aiand.com` and `api.doubleword.ai`. Health shows keys present; analyze returns Analysis incomplete. We merged your `qwen/qwen3.6-27b` + ai& call params. Please enable sandbox egress or document DEMO_MODE public deploy. Local Mac live path works for mouse/battery.
