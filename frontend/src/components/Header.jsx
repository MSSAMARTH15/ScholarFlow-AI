function Header() {
  return (
    <header className="header">
      <div className="brand">
        <div className="brand-icon">R</div>

        <div>
          <div className="brand-name">ResearchAI</div>
          <div className="brand-subtitle">
            Autonomous ML Research Agent
          </div>
        </div>
      </div>

      <div className="agent-status">
        <span className="status-dot"></span>
        Agent Ready
      </div>
    </header>
  );
}

export default Header;