export default function PhoneMockup() {
  return (
    <div
      className="phone"
      role="img"
      aria-label="DaddyFix AR interface: a water heater with an ELCB annotation locked in space, a live tracking status chip, and Scan / Reset controls"
    >
      <div className="phone-screen">
        <div className="screen-mesh"></div>
        <svg className="heater" viewBox="0 0 200 300" aria-hidden="true">
          <defs>
            <linearGradient id="tank" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#8b968f" />
              <stop offset="50%" stopColor="#c9d1cb" />
              <stop offset="100%" stopColor="#7c8983" />
            </linearGradient>
          </defs>
          <rect x="60" y="0" width="7" height="34" fill="#4a5651" />
          <rect x="133" y="0" width="7" height="34" fill="#4a5651" />
          <ellipse cx="100" cy="34" rx="70" ry="13" fill="#9aa59e" />
          <rect x="30" y="34" width="140" height="200" rx="16" fill="url(#tank)" stroke="#3a4642" strokeWidth="2" />
          <rect x="52" y="188" width="96" height="38" rx="6" fill="#1c2925" stroke="#4d5f58" strokeWidth="1.5" />
          <circle cx="72" cy="207" r="6" fill="#22C79F" />
          <rect x="88" y="200" width="42" height="4" fill="#4d5f58" />
          <rect x="88" y="209" width="30" height="4" fill="#4d5f58" />
          <rect x="18" y="234" width="164" height="10" rx="4" fill="#3a4642" />
        </svg>
        <div className="ar-line"></div>
        <div className="ar-reticle">
          <span className="ring"></span>
          <span className="core"></span>
        </div>
        <div className="ar-label">ELCB</div>

        <div className="hud-top">
          <div className="status-chip">
            <span className="status-dot"></span>
            <div className="status-text">
              <strong>Normal</strong>
              <span>LiDAR ready</span>
              <span>phase: reviewing</span>
            </div>
          </div>
          <div className="mesh-toggle">LiDAR mesh</div>
        </div>

        <div className="hud-bottom">
          <p className="hud-selected">Selected: ELCB</p>
          <p className="hud-item">Rinnai Water Heater</p>
          <p className="hud-status">Walk around — the pin stays locked in space.</p>
          <div className="hud-actions">
            <span className="btn-scan">Scan</span>
            <span className="btn-reset">Reset</span>
          </div>
        </div>
      </div>
      <div className="phone-btn phone-btn--left1"></div>
      <div className="phone-btn phone-btn--left2"></div>
      <div className="phone-btn phone-btn--right"></div>
    </div>
  );
}
