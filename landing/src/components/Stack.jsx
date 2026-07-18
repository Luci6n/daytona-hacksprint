const PARTNERS = [
  {
    role: "Sandbox & host",
    name: "Daytona",
    body: "Runs the FastAPI Daddy Agent on a public HTTPS sandbox. Every API key lives here — never on the phone.",
  },
  {
    role: "Vision",
    name: "Kimi",
    body: "Moonshot AI's vision model reads the frame, spots the failing part, and reasons about what's actually wrong.",
  },
  {
    role: "Parts data",
    name: "Oxylabs",
    body: "Fetches real manuals and buyable replacement parts for whatever Kimi identifies in the scene.",
  },
  {
    role: "GPU compute",
    name: "Nosana",
    body: "Optional heavy-compute lane for the vision pipeline when a job needs more than the sandbox CPU.",
  },
];

export default function Stack() {
  return (
    <section id="stack" className="stack-section">
      <div className="wrap">
        <div className="section-head">
          <span className="eyebrow">Cloud stack</span>
          <h2>Four partners, one Daddy Agent.</h2>
        </div>
        <div className="stack-grid">
          {PARTNERS.map((partner) => (
            <div className="stack-card" key={partner.name}>
              <span className="stack-role">Role: {partner.role}</span>
              <h3>{partner.name}</h3>
              <p>{partner.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
