import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)
def summarize_paper(title: str, content: str, research_question: str):

    prompt = f"""
You are an ML research paper analyzer.

Analyze the following research paper content.

Paper title:
{title}

Research question:
{research_question}

Paper content:
{content}


Extract the following information:

1. Research problem
2. Methodology
3. Machine learning models used
4. Dataset used
5. Evaluation metrics
6. Main results
7. Key findings
8. Limitations

Return ONLY valid JSON in exactly this format:

{{
    "research_problem": "...",
    "methodology": "...",
    "models_used": [],
    "dataset": "...",
    "evaluation_metrics": [],
    "main_results": "...",
    "key_findings": [],
    "limitations": "...",
    "relevance": "direct",
    "relevance_reason": "..."
}}
Evaluate whether this paper provides useful evidence for the specific research question above.

Use exactly one of these values for "relevance":

- "direct" = the paper directly investigates the same or very closely related problem and provides evidence that can directly answer the research question.
- "indirect" = the paper does not directly answer the research question, but provides useful supporting evidence about methods, datasets, evaluation, preprocessing, validation, interpretability, or related topics.
- "irrelevant" = the paper does not provide meaningful evidence for answering the research question.

Judge relevance against the research question, not merely whether the paper is related to machine learning.

For example, a paper about Shapley values or feature importance is indirect when the research question is about the best model for house-price prediction, unless the paper directly evaluates house-price prediction models.
"""

    response = llm.invoke(prompt)

    try:
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        return json.loads(text)

    except json.JSONDecodeError:

        print("Warning: Gemini returned invalid JSON.")

        print("Raw response:")
        print(response.text)

        return {
        "research_problem": "Not specified",
        "methodology": "Not specified",
        "models_used": [],
        "dataset": "Not specified",
        "evaluation_metrics": [],
        "main_results": "Not specified",
        "key_findings": [],
        "limitations": "Could not parse model response",
        "relevance": "irrelevant",
        "relevance_reason": "Could not determine relevance because the paper response could not be parsed."
}
        


if __name__ == "__main__":

    from app.tools.extractor import extract_content

    test_title = "A Multi-Modal Deep Learning Based Approach for House Price Prediction"

    test_url = "https://arxiv.org/html/2409.05335v1"

    print("Extracting paper...")

    test_content = extract_content(test_url)

    print("Paper extracted successfully.")
    print("Generating summary...")

    result = summarize_paper(
    test_title,
    test_content,
    "What is the best machine learning model for predicting house prices?"
)

    print("\nPaper Summary:")
    print(json.dumps(result, indent=2))