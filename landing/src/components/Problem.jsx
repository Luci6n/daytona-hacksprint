const ITEMS = [
  {
    title: "Not spatial",
    body: "A PDF diagram shows a generic unit. It doesn't show which pipe, which panel, which part is failing behind your wall.",
  },
  {
    title: "Not static",
    body: "A drip, a trip, a reset that won't hold — these change while you watch. One photo can't prove a leak is still happening.",
  },
  {
    title: "Wrong part, twice",
    body: "Guess the part number and you're driving to the hardware store twice. Spatial ID means you buy the right one the first time.",
  },
];

export default function Problem() {
  return (
    <>
      <hr className="rule" />
      <section id="problem">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">Why manuals fail</span>
            <h2>Repairs aren't flat, and they don't hold still.</h2>
          </div>
          <div className="problem-grid">
            {ITEMS.map((item) => (
              <div className="problem-item" key={item.title}>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
