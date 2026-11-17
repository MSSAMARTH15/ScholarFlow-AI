import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./ResearchReport.css";

function ResearchReport({ result, onNewResearch }) {
  const [showPlan, setShowPlan] = useState(false);
  const [showSources, setShowSources] = useState(true);
  const [copied, setCopied] = useState(false);

  const papers = useMemo(() => {
    try {
      const data =
        typeof result.research_results === "string"
          ? JSON.parse(result.research_results)
          : result.research_results || [];

      return data.flatMap((task) =>
        (task.results || []).map((paper) => ({
          ...paper,
          researchTask: task.task,
        }))
      );
    } catch {
      return [];
    }
  }, [result.research_results]);

  const plan = Array.isArray(result.plan) ? result.plan : [];

  /*
   * Clean HTML <br> tags returned by the research agent
   * before sending the response to ReactMarkdown.
   */
  const markdownResponse = (result.response || "")
    .replace(/<br\s*\/?>/gi, " • ")
    .replace(/&lt;br\s*\/?&gt;/gi, " • ");

  const getTaskName = (task) =>
    typeof task === "string" ? task : task.task || "Research task";

  async function copyAnswer() {
    try {
      await navigator.clipboard.writeText(result.response || "");
      setCopied(true);

      setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  function downloadReport() {
    const content = result.response || "No research response available.";

    const blob = new Blob([content], {
      type: "text/markdown;charset=utf-8",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "research-report.md";
    link.click();

    URL.revokeObjectURL(url);
  }

  return (
    <main className="report-page">
      <div className="report-toolbar">
        <button className="report-back" onClick={onNewResearch}>
          ← New Research
        </button>

        <span className="report-status">
          <span className="report-status-dot" />
          Research complete
        </span>
      </div>

      <section className="report-hero">
        <div className="report-eyebrow">RESEARCH REPORT</div>

        <h1>{result.message || "Research Results"}</h1>

        <p>
          Evidence gathered, analyzed, and synthesized by your
          autonomous research agent.
        </p>

        {result.output_requirements && (
          <details className="report-requirements">
            <summary>View output instructions</summary>
            <p>{result.output_requirements}</p>
          </details>
        )}
      </section>

      <section className="report-stats">
        <div className="report-stat">
          <span className="stat-label">Research tasks</span>
          <strong>{plan.length}</strong>
          <span className="stat-caption">
            Tasks in the research plan
          </span>
        </div>

        <div className="report-stat">
          <span className="stat-label">Analyzed sources</span>
          <strong>{papers.length}</strong>
          <span className="stat-caption">
            Successfully summarized sources
          </span>
        </div>

        <div className="report-stat">
          <span className="stat-label">Report status</span>
          <strong className="stat-ready">Ready</strong>
          <span className="stat-caption">
            Synthesis generated
          </span>
        </div>
      </section>

      <section className="report-answer panel">
        <div className="panel-heading">
          <div>
            <span className="section-kicker">FINAL ANALYSIS</span>
            <h2>Research synthesis</h2>
          </div>

          <div className="report-actions">
            <button onClick={copyAnswer}>
              {copied ? "Copied!" : "Copy"}
            </button>

            <button onClick={downloadReport}>
              Export Markdown ↓
            </button>
          </div>
        </div>

        <article className="markdown-content">
          {result.response ? (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                a: ({ href, children, ...props }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    {...props}
                  >
                    {children}
                  </a>
                ),
              }}
            >
              {markdownResponse}
            </ReactMarkdown>
          ) : (
            <p>The agent did not return a final response.</p>
          )}
        </article>
      </section>

      <section className="report-section panel">
        <button
          className="collapsible-heading"
          onClick={() => setShowPlan(!showPlan)}
          aria-expanded={showPlan}
        >
          <div>
            <span className="section-kicker">RESEARCH PROCESS</span>

            <h2>Research plan</h2>

            <p>
              {plan.length} tasks generated by the planner
            </p>
          </div>

          <span className="collapse-icon">
            {showPlan ? "−" : "+"}
          </span>
        </button>

        {showPlan && (
          <div className="plan-list">
            {plan.map((task, index) => (
              <div className="plan-item" key={index}>
                <span className="plan-number">
                  {String(index + 1).padStart(2, "0")}
                </span>

                <span>{getTaskName(task)}</span>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="report-section panel">
        <button
          className="collapsible-heading"
          onClick={() => setShowSources(!showSources)}
          aria-expanded={showSources}
        >
          <div>
            <span className="section-kicker">EVIDENCE LIBRARY</span>

            <h2>Research sources</h2>

            <p>
              Papers and technical sources collected during research
            </p>
          </div>

          <span className="collapse-icon">
            {showSources ? "−" : "+"}
          </span>
        </button>

        {showSources && (
          <div className="source-list">
            {papers.length === 0 ? (
              <p className="empty-sources">
                No successfully summarized sources were returned.
              </p>
            ) : (
              papers.map((paper, index) => {
                const summary =
                  typeof paper.summary === "object" &&
                  paper.summary !== null
                    ? paper.summary
                    : {};

                const relevance = summary.relevance;

                return (
                  <article
                    className="source-card"
                    key={`${paper.url}-${index}`}
                  >
                    <div className="source-card-top">
                      <span className="source-index">
                        SOURCE {String(index + 1).padStart(2, "0")}
                      </span>

                      {relevance && (
                        <span className="source-relevance">
                          {relevance}
                        </span>
                      )}
                    </div>

                    <h3>
                      {paper.title || "Untitled source"}
                    </h3>

                    {paper.snippet && (
                      <p className="source-snippet">
                        {paper.snippet}
                      </p>
                    )}

                    {summary.relevance_reason && (
                      <p className="source-reason">
                        {summary.relevance_reason}
                      </p>
                    )}

                    {paper.url && (
                      <a
                        className="source-link"
                        href={paper.url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Open original source ↗
                      </a>
                    )}
                  </article>
                );
              })
            )}
          </div>
        )}
      </section>

      <footer className="report-footer">
        <span>ResearchAI</span>
        <span>Evidence-based research synthesis</span>
      </footer>
    </main>
  );
}

export default ResearchReport;