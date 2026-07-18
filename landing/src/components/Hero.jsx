import PhoneMockup from "./PhoneMockup";

export default function Hero() {
  return (
    <header className="hero">
      <div className="wrap">
        <div className="hero-copy">
          <span className="eyebrow">Spatial AR Home Repair</span>
          <h1>
            Point at the
            <br />
            problem. <em>See</em>
            <br />
            the fix.
          </h1>
          <p className="hero-sub">
            LiDAR pins the failing part in real 3D space on your iPhone. A cloud agent
            on Daytona reasons about what's wrong and walks you through fixing it —
            without a single API key ever touching the phone.
          </p>
          <p className="hero-platform">iPhone 17 Pro · LiDAR + ARKit · RealityKit</p>
        </div>
        <div className="phone-stage">
          <PhoneMockup />
        </div>
      </div>
    </header>
  );
}
