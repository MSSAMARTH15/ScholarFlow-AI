import { useState } from "react";

function ResearchForm({ onResult, onLoading }) {
  const [question, setQuestion] = useState("");
  const [requirements, setRequirements] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!question.trim()) return;

    onLoading(true);
    onResult(null);

    try {
      const response = await fetch("http://127.0.0.1:5000/api/research", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question.trim(),
          output_requirements: requirements.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Research request failed");
      }

      onResult(data.result);
    } catch (error) {
      console.error("Research error:", error);

      onResult({
        error: error.message,
      });
    } finally {
      onLoading(false);
    }
  };

  return (
    <form className="research-form" onSubmit={handleSubmit}>
      <div className="form-header">
        <div>
          <h2>Start a Research Task</h2>
          <p>Give the agent a question to investigate.</p>
        </div>

        <span className="langgraph-badge">● LangGraph</span>
      </div>

      <label>Research Question</label>

      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="e.g. Compare YOLOv5, YOLOv8 and YOLOv11 for small object detection..."
        rows={5}
      />

      <div className="label-row">
        <label>Output Requirements</label>
        <span>Optional</span>
      </div>

      <textarea
        value={requirements}
        onChange={(e) => setRequirements(e.target.value)}
        placeholder="e.g. Give me a comparison table with metrics, advantages, limitations, and sources."
        rows={4}
      />

      <button type="submit" disabled={!question.trim()}>
        Start Research
        <span>→</span>
      </button>
    </form>
  );
}

export default ResearchForm;