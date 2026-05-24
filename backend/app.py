import requests
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
# SYSTEM_PROMPT = """Below is a statement. Analyze its sentiment and output a strict decimal score between 0.0 (extremely negative/furious) and 1.0 (extremely positive/thrilled). Do not include any other text or explanation."""

# Helper functions
def get_raw_output(text):
    prompt = f"""
    Below is a statement.
    Analyze its sentiment and output ONLY a decimal score between 0.0 and 1.0.

    Statement:
    {text}

    Score:
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "vibecheck",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]


def extract_score(text):
    # Extract a decimal score from the text
    matches = re.findall(r"\b(?:0(?:\.\d+)?|1(?:\.0+)?)\b", text)
    if not matches:
        return 0.5

    return float(matches[0])


def sentiment_score(text):
    raw = get_raw_output(text)
    return extract_score(raw)

# Routes
@app.route("/")
def home():
    return """
    <h1>VibeCheck API</h1>
    <form action="/test" method="post">
        <input name="message">
        <button type="submit">Send</button>
    </form>
    """

@app.route("/test", methods=["POST"])
def test():
    message = request.form["message"]
    raw_output = get_raw_output(message)
    score = extract_score(raw_output)

    return f"""
    <h2>Sentiment Score:</h2>
    <p>{score}</p>

    <h3>Raw Model Output:</h3>
    <p>{raw_output}</p>
    """

@app.route("/chat", methods=["POST"])
def chat():
    if not request.json or "message" not in request.json:
        return jsonify({"error": "Missing message"}), 400

    user_message = request.json["message"]

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "vibecheck",
                "prompt": user_message,
                "stream": False
            }
        )

        data = response.json()
        return jsonify({
            "reply": data["response"]
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app.route("/sentiment", methods=["POST"])
def sentiment():
    if not request.json or "message" not in request.json:
        return jsonify({"score": 0.5})

    text = request.json["message"]
    score = sentiment_score(text)

    return jsonify({
        "score": score
    })


if __name__ == "__main__":
    app.run(debug=True)