# DaddyFix — Local Xcode Install & Run Guide

For **Kenji** and **Brian** (Mac).  
**Lucian is on Windows** and does **not** install Xcode — use the backend guide instead.

> **LiDAR note:** The iOS Simulator has **no LiDAR**. You can compile on Simulator, but the hero demo must run on a **Pro iPhone with LiDAR**.

---

## 1. Requirements checklist

| Requirement | Minimum | Notes |
|-------------|---------|--------|
| Mac | Apple Silicon or Intel | macOS that supports **Xcode 16+** |
| Free disk | **~25–40 GB** | Xcode alone is ~10–15+ GB + downloads |
| Xcode | **16+** | Full app from App Store (not only CLI tools) |
| Apple ID | Free is OK | Needed to sign and run on a real iPhone |
| iPhone (demo) | **LiDAR Pro** + **iOS 18+** | 12/13/14/15/16/17 **Pro / Pro Max** |
| Cable | USB-C or Lightning | Trust computer on first plug-in |

Project settings in this repo:

- Deployment target: **iOS 18.0**
- Bundle ID (default): `com.daddyfix.app`
- Camera permission: already in `Info.plist`
- ARKit required capability: already set

---

## 2. Install Xcode (first time, ~30–90 min)

### Step A — App Store

1. Open **Mac App Store**.
2. Search **Xcode**.
3. Click **Get / Install** (or **Update** if you have an older version).
4. Wait for download + install. Leave Mac plugged in and awake if possible.

### Step B — First launch

1. Open **Xcode** from Applications (or Spotlight: `⌘Space` → “Xcode”).
2. Accept the license agreement.
3. If prompted, install **additional components** (simulators, platforms) — allow it.
4. Sign in: **Xcode → Settings… → Accounts → + → Apple ID**.

### Step C — Point Terminal at full Xcode

Open **Terminal** and run:

```bash
# Install CLT if missing (optional but useful)
xcode-select --install

# Point developer tools at the full Xcode app (not just CLT)
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer

# Accept license (non-interactive)
sudo xcodebuild -license accept

# Confirm version (want 16.x or newer)
xcodebuild -version
```

**Good output example:**

```text
Xcode 16.2
Build version 16C...
```

**Bad output:**  
`requires Xcode, but active developer directory is a command line tools instance`  
→ re-run the `xcode-select -s` line above.

### Step D — Install iOS platform (if Xcode asks)

In Xcode:

1. **Xcode → Settings… → Platforms** (or **Components** on some versions).
2. Install **iOS 18** (or the latest matching platform).
3. Wait until download finishes before building.

---

## 3. Clone the project

```bash
# If you don't have the repo yet
git clone https://github.com/Luci6n/daytona-hacksprint.git
cd daytona-hacksprint

# If you already have it
cd /path/to/daytona-hacksprint
git pull origin main
```

---

## 4. Open the Xcode project

```bash
cd /path/to/daytona-hacksprint
open DaddyFix/DaddyFix.xcodeproj
```

Use **`DaddyFix.xcodeproj`** — that is the project file.  
Do **not** open a random folder of Swift files only.

---

## 5. Signing (required to run on a real iPhone)

In Xcode:

1. Left sidebar: click the blue **DaddyFix** project icon.
2. Under **TARGETS**, select **DaddyFix**.
3. Open the **Signing & Capabilities** tab.
4. Check **Automatically manage signing**.
5. **Team**: pick your Apple ID personal team.
   - If empty: **Add Account…** → sign in with Apple ID → pick the team.
6. If Bundle ID conflicts (`com.daddyfix.app` already used), change it to something unique, e.g.:
   - `com.yourname.daddyfix`

You do **not** need a paid Apple Developer Program membership for personal-device testing during the hackathon (free Apple ID is enough for your own phone).

---

## 6. Connect iPhone & enable Developer Mode

### On the Mac

1. Plug in the iPhone with a cable.
2. Unlock the phone → tap **Trust** this computer if asked.
3. In Xcode’s device menu (top toolbar, next to the scheme **DaddyFix**), select **your iPhone** (not “Any iOS Simulator”).

### On the iPhone (iOS 16+)

1. **Settings → Privacy & Security → Developer Mode** → **On**.
2. Reboot if prompted, then confirm **Turn On**.
3. After first install: **Settings → General → VPN & Device Management** (or **Device Management**) → trust your developer certificate.

---

## 7. Build & run

1. Destination = your **physical iPhone**.
2. Press **Run**: toolbar ▶ or **`⌘R`**.
3. Wait for build + install.
4. On first launch, accept **Camera** permission (required for AR + LiDAR).

### Smoke test (Brian AR scaffold)

You should roughly see:

1. Coaching overlay while planes are detected  
2. Status chip like **LiDAR ready** on Pro devices  
3. Mock ELCB highlight / arrow (auto or via **Place mock ELCB**)  
4. **LiDAR mesh** toggle for demo narration  
5. Walk around → annotations stay locked  
6. Tap highlight → selection status  

AR-specific details: [`BRIAN_SETUP.md`](./BRIAN_SETUP.md).

---

## 8. Simulator (optional, limited)

You *can* select an **iPhone 16 Pro** simulator and press **`⌘R`** to verify UI compiles.

Limitations:

- **No LiDAR / real depth mesh**
- Camera is fake / limited
- **Not valid for the hero demo**

Always do a real-device run before judging.

---

## 9. Common problems & fixes

| Symptom | Fix |
|---------|-----|
| Xcode too old / can’t open project | Install Xcode **16+** from App Store |
| `active developer directory is a command line tools instance` | `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer` |
| No Team / signing errors | Xcode → Settings → Accounts → add Apple ID; enable automatic signing |
| Bundle ID conflict | Change to `com.YOURNAME.daddyfix` |
| “Failed to prepare device” | Unlock phone, replug cable, trust computer, enable Developer Mode |
| Developer Mode missing | Update iPhone iOS; Settings → Privacy & Security |
| Black screen / no camera | Grant Camera for DaddyFix; run on **device**, not simulator |
| `isLiDARAvailable == false` | Use a **Pro** LiDAR phone; don’t use simulator destination |
| Build fails on deployment target | Need iOS **18** device/SDK; install platform in Xcode Settings → Platforms |
| Disk full | Free 20+ GB; delete old Xcode / unused simulators (**Xcode → Settings → Platforms**) |
| App won’t open after install | Settings → General → VPN & Device Management → Trust developer |

---

## 10. Day-to-day workflow

```bash
cd /path/to/daytona-hacksprint
git pull origin main
open DaddyFix/DaddyFix.xcodeproj
# edit your owned files only → ⌘R on device
```

**Ownership reminder** (see root `AGENTS.md`):

| Person | Edit these |
|--------|------------|
| **Brian** | `DaddyFix/DaddyFix/AR/*` |
| **Kenji** | Views, AppState, Voice, x402, iOS `VisionService` client |
| **Lucian** | Backend only (Windows) — no Xcode |

---

## 11. Quick verify commands

```bash
# Xcode path + version
xcode-select -p
xcodebuild -version

# List connected devices (after Xcode is set up)
xcrun xctrace list devices

# Open project
open DaddyFix/DaddyFix.xcodeproj
```

---

## 12. Done checklist

- [ ] Xcode 16+ installed and opens without errors  
- [ ] `xcodebuild -version` shows Xcode 16+  
- [ ] Apple ID added in Xcode Accounts  
- [ ] Project signing has a Team  
- [ ] iPhone: Developer Mode on + trusted  
- [ ] App builds with **`⌘R`** on device  
- [ ] Camera permission accepted  
- [ ] (Demo) LiDAR Pro phone shows mesh / locked annotations  

You’re ready to build. For AR-specific coding tasks, continue in [`BRIAN_SETUP.md`](./BRIAN_SETUP.md).
