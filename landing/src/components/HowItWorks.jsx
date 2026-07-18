export default function HowItWorks() {
  return (
    <>
      <hr className="rule" />
      <section id="how">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">Architecture</span>
            <h2>Thin client. Fat cloud agent.</h2>
          </div>
          <div className="schematic">
            <div className="node">
              <span className="node-eyebrow">01 · On device</span>
              <h3>iPhone 17 Pro</h3>
              <p>LiDAR · ARKit · RealityKit captures a frame or a live event stream.</p>
            </div>
            <div className="wire">
              <span className="wire-label">HTTPS · JPEG frame / event</span>
            </div>
            <div className="node node--cloud">
              <span className="node-eyebrow">02 · In the cloud</span>
              <h3>Daytona Sandbox</h3>
              <p>The Daddy Agent reasons: Kimi vision, Oxylabs parts, Nosana GPU.</p>
            </div>
            <div className="wire">
              <span className="wire-label">AnalysisResult JSON</span>
            </div>
            <div className="node">
              <span className="node-eyebrow">03 · Back on device</span>
              <h3>AR lock-in</h3>
              <p>placeAnnotations() pins the answer to a world anchor. It stays put.</p>
            </div>
          </div>
          <div className="modes">
            <div className="mode">
              <strong>POST /analyze — one-shot</strong>
              <span>Single JPEG in → full AnalysisResult out. The safe baseline for the water-heater demo.</span>
            </div>
            <div className="mode">
              <strong>POST /stream/phone/event — live</strong>
              <span>Frames every ~2s, keyed by sessionId → AR annotations refresh as the event unfolds.</span>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
