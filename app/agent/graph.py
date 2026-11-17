import os
import json
from typing import TypedDict

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

from app.tools.search import search_web
from app.tools.extractor import extract_content
from app.tools.summarizer import summarize_paper

load_dotenv()

print("Gemini API key loaded:", bool(os.getenv("GEMINI_API_KEY")))


class AgentState(TypedDict):
    message: str
    output_requirements: str
    plan: list[str]
    research_results: str
    response: str

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY")
)


# --------------------------------------------------
# PLANNER NODE
# --------------------------------------------------

def planner_node(state: AgentState):

    prompt = f"""
You are an ML research planner.

Break the following research question into 3-5 concrete research tasks.

For each task, create a concise search query that can be used
to find relevant research papers, datasets, experiments, or
technical sources.

Return ONLY valid JSON.
Do not include markdown.
Do not include explanations.

Return exactly this format:

[
    {{
        "task": "Describe the research task",
        "search_query": "Concise search query"
    }}
]

Research question:
{state["message"]}
"""

    response = llm.invoke(prompt)

    plan = json.loads(response.text)

    return {
        "plan": plan
    }

# --------------------------------------------------
# RESEARCH NODE
# --------------------------------------------------

# --------------------------------------------------
# RESEARCH NODE
# --------------------------------------------------

def research_node(state: AgentState):

    research_results = []

    for task in state["plan"]:

        # Support both old-style string tasks and
        # new-style dictionary tasks
        if isinstance(task, dict):
            task_description = task.get("task", "")
            search_query = task.get("search_query", task_description)
        else:
            task_description = task
            search_query = task

        print(f"\nSearching for: {task_description}")

        results = search_web(search_query)
        print(f"Found {len(results)} search results")

        task_results = []

        for result in results:

            url = result.get("url")

            if not url:
                continue

            try:

                print(f"Attempting extraction: {url}")

                content = extract_content(url)

                if not content:
                    print(f"No content extracted: {url}")
                    continue

                print(f"Extracting: {result.get('title')}")

                # Pass the ORIGINAL research question
                # to the summarizer so relevance can be judged
                summary = summarize_paper(
                    result.get("title", "Unknown"),
                    content[:12000],
                    state["message"]
                )

                # --------------------------------------------------
                # FILTER SOURCES BASED ON RELEVANCE
                # --------------------------------------------------

                relevance = summary.get("relevance", "irrelevant")

                if relevance not in ["direct", "indirect"]:

                    print(
                        f"Skipping irrelevant source: "
                        f"{result.get('title')}"
                    )

                    continue


                # --------------------------------------------------
                # KEEP ONLY SUCCESSFULLY SUMMARIZED SOURCES
                # --------------------------------------------------

                task_results.append({
                    "title": result.get("title", "Unknown"),
                    "url": url,
                    "snippet": result.get("snippet", ""),
                    "summary": summary
                })
                print(
    f"ADDED TO TASK RESULTS: {len(task_results)}"
)
                
                print(
                    f"Summarized: {result.get('title')} "
                    f"[{relevance}]"
                )

            except Exception as e:

                print(
                    f"ERROR processing {url}: {type(e).__name__}: {e}"
                )

            import traceback
            traceback.print_exc()

            
                # IMPORTANT:
                # Do NOT add failed sources to research_results.

            continue

        print(
            f"TASK COMPLETE: {task_description}"
)
        print(
    f"SUCCESSFUL RESULTS: {len(task_results)}"
)
        
        research_results.append({
            "task": task_description,
            "results": task_results
        })


    research_text = json.dumps(
        research_results,
        indent=2
    )

    return {
        "research_results": research_text
    }
# --------------------------------------------------
# ANSWER NODE
# --------------------------------------------------

def answer_node(state: AgentState):

    prompt = f"""
You are an AI/ML research synthesis agent.

Original research question:
{state["message"]}

Research plan:
{json.dumps(state["plan"], indent=2)}

Research evidence collected from papers:
{state["research_results"]}

User's requested output format/instructions:
{state["output_requirements"]}

Your job is to synthesize the research evidence and answer the
original research question according to the user's requested
output format.



IMPORTANT RULES:

1. Use ONLY information contained in the research evidence.

2. Do NOT use outside knowledge.

3. Do NOT invent model performance numbers.

4. Do NOT invent datasets, models, results, limitations, or sources.

5. Do NOT fabricate citations or URLs.

6. Prefer concrete numerical results when they are available.

7. Mention datasets, models, and evaluation metrics when relevant.

8. Only discuss advantages and limitations that are supported by
   the research evidence.

9. NEVER declare a model to be universally "the best" unless the
   research evidence contains a fair comparison supporting that
   conclusion.

10. If models are compared within the SAME study using the SAME
    dataset, evaluation metric, and evaluation setup, you may state
    which model performed better in that study.

11. Use all relevant research evidence collected in
    state["research_results"]. Do not ignore successfully
    summarized sources when they are relevant to the original
    research question.

12. When models come from different studies, clearly explain that
    their numerical results are not directly comparable.

13. If a model is the best-performing model within one particular
    study, describe it as:
    "the best-performing model in that study"
    rather than:
    "the best model overall."

14. Distinguish clearly between:
    - Direct evidence reported by a paper
    - Qualitative synthesis across multiple papers

15. NEVER present a synthesized conclusion as if it were directly
    stated by a paper.

16. If different papers reach different conclusions, explain why
    they may differ based ONLY on the evidence provided.

17. If the evidence is insufficient to answer a part of the user's
    question, say:
    "The available research evidence is insufficient to determine this."

18. If the user requests a comparison table, include only information
    supported by the research evidence.

19. If numerical results are unavailable for a model, write:
    "Not reported in the available evidence"
    instead of guessing.

20. Do NOT force every model into the table if the available evidence
    does not contain enough information to support the requested fields.

21. The user's output instructions are authoritative for presentation.
    Follow the requested format, table, bullet points, word limit,
    tone, and level of detail.

22. Do NOT force a predefined structure such as:
    Conclusion, Evidence, Model Comparison, Important Factors,
    or Limitations unless the user explicitly requests that structure.

23. Keep the answer focused on the original research question.

24. Every model, numerical result, dataset, metric, advantage,
    limitation, and source included in the final answer must be
    traceable to at least one entry in state["research_results"].

25. Do not use information merely because it appears in a search
    result title, URL, or the model's prior knowledge. Use it only
    if it is present in the summarized research evidence stored
    in state["research_results"].

26. When making the final synthesis, consider the relevant evidence
    from ALL successfully summarized sources before reaching a
    conclusion.

27. If the evidence supports a strong candidate but does not support
    a universally best model, explicitly state that distinction.

28. Do NOT claim that a study found a model superior unless that
    comparison is explicitly supported by the research evidence
    collected for that study.

29. When the research evidence contains concrete numerical results
    from a fair within-study comparison, prioritize including those
    results in the final comparison table over sources that provide
    only qualitative conclusions.

30. When multiple relevant studies are available, include the
    strongest directly relevant evidence first, especially studies
    that compare multiple models on the same dataset using the same
    evaluation metric.

31. When the same model appears in multiple studies, treat each
    study's result as a separate piece of evidence. Do not combine
    or generalize the results across studies unless the research
    evidence explicitly supports doing so.

32. When making a qualitative statement such as "tree-based models
    perform strongly" or "deep learning performs better", identify
    the specific study or studies supporting that statement and do
    not generalize beyond their reported scope.

33. Avoid introducing general machine learning claims in the synthesis
    unless they are explicitly supported by the collected research
    evidence. In particular, do not infer that one model family
    generally handles a property better than another unless the
    evidence contains that comparison.
    
Before producing the answer, internally check:


- Are all claims supported by the research evidence?
- Are numerical results copied only from the evidence?
- Are numerical results from different datasets being kept separate?
- Is any "best" claim limited to the study where it was demonstrated?
- Are advantages and limitations supported by the evidence?
- Are sources and URLs taken directly from the research evidence?

If any information is unsupported, remove it or state that the
available research evidence is insufficient.

Generate the final answer now.
"""

    response = llm.invoke(prompt)

    return {
        "response": response.text
    }
# --------------------------------------------------
# BUILD LANGGRAPH
# --------------------------------------------------

builder = StateGraph(AgentState)

builder.add_node("planner", planner_node)
builder.add_node("research", research_node)
builder.add_node("answer", answer_node)

builder.add_edge(START, "planner")
builder.add_edge("planner", "research")
builder.add_edge("research", "answer")
builder.add_edge("answer", END)

graph = builder.compile()


# --------------------------------------------------
# RUN AGENT
# --------------------------------------------------

if __name__ == "__main__":

    research_question = input(
        "\nEnter your research question:\n> "
    ).strip()

    output_requirements = input(
        "\nHow would you like the output? "
        "(Press Enter for default format)\n> "
    ).strip()

    # Use default output instructions if the user
    # doesn't provide any custom requirements.
    if not output_requirements:
        output_requirements = """
Provide a clear research synthesis with:
- Conclusion
- Evidence from research
- Model comparison
- Important factors
- Limitations
- Sources
"""

    print("\nStarting research...\n")

    result = graph.invoke({
        "message": research_question,
        "output_requirements": output_requirements
    })

    print("\n" + "=" * 60)
    print("RESEARCH PLAN")
    print("=" * 60)

    for i, task in enumerate(result["plan"], 1):
        print(f"{i}. {task}")

    print("\n" + "=" * 60)
    print("RESEARCH RESULTS")
    print("=" * 60)

    print(result["research_results"])

    print("\n" + "=" * 60)
    print("FINAL RESPONSE")
    print("=" * 60)

    print(result["response"])
    