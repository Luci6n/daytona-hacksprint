export default function Nav() {
  return (
    <nav className="site-nav">
      <div className="wrap">
        <div className="wordmark">
          Daddy<span>Fix</span>
        </div>
        <ul className="nav-links">
          <li><a href="#problem">Problem</a></li>
          <li><a href="#how">How it works</a></li>
          <li><a href="#stack">Stack</a></li>
        </ul>
        <span className="nav-tag">v0.2 · Hackathon MVP</span>
      </div>
    </nav>
  );
}
