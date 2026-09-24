from flask import Flask, request, jsonify, render_template
import requests
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

API_KEY = os.environ.get("OPENROUTER_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    # Optional: Add jailbreak system prompt if needed
    system_prompt = "You are NIMA AI, a helpful assistant."

    payload = {
        "model": "deepseek/deepseek-r1",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60
        )
        app.logger.info(f"OpenRouter response status: {r.status_code}")
        app.logger.info(f"OpenRouter response body: {r.text[:500]}")
        
        if r.status_code != 200:
            return jsonify({
                "error": f"API error {r.status_code}",
                "details": r.json().get("error", {}).get("message", "No details")
            }), r.status_code
        
        return jsonify(r.json())
    
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request failed: {str(e)}")
        return jsonify({"error": "Request to OpenRouter failed", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
