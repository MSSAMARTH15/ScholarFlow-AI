import { useState } from "react";
import Header from "./components/Header";
import ResearchForm from "./components/ResearchForm";
import ExampleQueries from "./components/ExampleQueries";
import ResearchReport from "./components/ResearchReport";
import "./App.css";

function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  function handleNewResearch() {
    setResult(null);
    setLoading(false);
  }

  return (
    <div className="app">
      <Header />

      {!result && !loading && (
        <main>
          <section className="hero">
            <div className="eyebrow">
              <span className="eyebrow-dot" />
              AI-POWERED RESEARCH
            </div>

            <h1>
              Research smarter.
              <br />
              <span>Discover faster.</span>
            </h1>

            <p>
              Ask a research question and let the autonomous agent
              find, extract, analyze, and synthesize relevant research.
            </p>
          </section>

          <ResearchForm
            onResult={setResult}
            onLoading={setLoading}
          />

          <ExampleQueries />
        </main>
      )}

      {loading && (
        <main className="loading-page">
          <div className="loading-indicator" />

          <div className="eyebrow">RESEARCH IN PROGRESS</div>
          <h1>Working on your research</h1>

          <p>
            Your agent is planning searches, extracting sources,
            summarizing evidence, and preparing the synthesis.
            This can take a few minutes.
          </p>

          <div className="loading-steps">
            <span>01&nbsp; Plan</span>
            <span>02&nbsp; Research</span>
            <span>03&nbsp; Synthesize</span>
          </div>
        </main>
      )}

      {result && !loading && (
        result.error ? (
          <main className="error-page">
            <div className="eyebrow">RESEARCH INTERRUPTED</div>
            <h1>We couldn't complete the research.</h1>
            <p>{result.error}</p>

            <button
              className="research-button"
              onClick={handleNewResearch}
            >
              Back to Research
            </button>
          </main>
        ) : (
          <ResearchReport
            result={result}
            onNewResearch={handleNewResearch}
          />
        )
      )}
    </div>
  );
}

export default App;