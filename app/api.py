from flask import Flask, request, jsonify
from flask_cors import CORS

from app.agent.graph import graph

app = Flask(__name__)
CORS(app)


@app.route("/api/research", methods=["POST"])
def research():
    try:
        data = request.get_json() or {}

        question = data.get("question", "").strip()
        output_requirements = data.get("output_requirements", "").strip()

        if not question:
            return jsonify({
                "success": False,
                "error": "Research question is required"
            }), 400

        initial_state = {
    "message": question,
    "output_requirements": output_requirements
}

        print("\n" + "=" * 60)
        print("RESEARCH REQUEST")
        print("=" * 60)
        print("Question:", question)
        print("Output requirements:", output_requirements)
        print("=" * 60)

        result = graph.invoke(initial_state)

        print("\nResearch completed successfully.")

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as e:
        print("\n" + "=" * 60)
        print("RESEARCH ERROR")
        print("=" * 60)
        print("Error type:", type(e).__name__)
        print("Error:", str(e))
        print("=" * 60)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "ResearchAI backend is running"
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )