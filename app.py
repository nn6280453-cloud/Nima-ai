# ----------------------------------------------------
# app.py
# ----------------------------------------------------
import os
import json
import logging
import requests
from flask import Flask, request, jsonify, abort

# -----------------------------------------------------------------
# 1️⃣  Configuration & logging
# -----------------------------------------------------------------
app = Flask(__name__)

# Log everything to stdout – Render collects this automatically
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler()]
)

# -----------------------------------------------------------------
# 2️⃣  Helper: fetch the OpenRouter API key
# -----------------------------------------------------------------
def get_openrouter_key() -> str:
    """
    Returns the OpenRouter API key.
    1. Looks for OPENROUTER_API_KEY in the environment.
    2. If not found, falls back to the hard‑coded key you supplied.
    """
    key = os.getenv("OPENROUTER_API_KEY")
    if key:
        return key
    # Hard‑coded key – **only for quick testing**.
    # In production, delete this line and set OPENROUTER_API_KEY in env.
    return "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"

OPENROUTER_KEY = get_openrouter_key()

# -----------------------------------------------------------------
# 3️⃣  /ask endpoint – forwards user messages to OpenRouter
# -----------------------------------------------------------------
@app.route("/ask", methods=["POST"])
def ask():
    """
    Expected JSON body:
    {
        "message": "Your question here"
    }
    Returns:
    {
        "reply": "OpenRouter answer"
    }
    """
    # 3.1  Validate request body
    if not request.is_json:
        logging.warning("Non‑JSON request received")
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json(silent=True)
    if not data or "message" not in data:
        logging.warning("Missing 'message' key in JSON")
        return jsonify({"error": "Missing 'message' field"}), 400

    user_message = data["message"]
    logging.info(f"Received /ask request – user message: {user_message}")

    # 3.2  Prepare the OpenRouter payload
    payload = {
        "model": "deepseek/deepseek-r1",  # you can change the model if you want
        "messages": [
            {"role": "system", "content": "You are NIMA AI, a helpful cybersecurity assistant."},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 1024
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # 3.3  Call OpenRouter
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60  # 60 s timeout – adjust as needed
        )
        response.raise_for_status()  # raises HTTPError for 4xx/5xx

        resp_json = response.json()
        reply = resp_json.get("choices", [{}])[0].get("message", {}).get("content")

        if reply is None:
            raise ValueError("OpenRouter response missing reply text")

        logging.info("OpenRouter reply received")
        return jsonify({"reply": reply})

    except requests.exceptions.RequestException as e:
        # network error, timeout, bad status code, etc.
        logging.error(f"OpenRouter request failed: {e}")
        return jsonify({"error": "Failed to contact OpenRouter"}), 502
    except (ValueError, KeyError, IndexError) as e:
        # malformed response
        logging.error(f"OpenRouter response parsing error: {e}")
        return jsonify({"error": "OpenRouter returned an unexpected response"}), 502
    except Exception as e:
        # catch‑all for any other bug
        logging.exception("Unexpected error in /ask")
        return jsonify({"error": "Internal server error"}), 500

# -----------------------------------------------------------------
# 4️⃣  Optional health‑check route (helps Render / Heroku etc.)
# -----------------------------------------------------------------
@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

# -----------------------------------------------------------------
# 5️⃣  Run the Flask app locally (for dev)
# -----------------------------------------------------------------
if __name__ == "__main__":
    # Render expects the app to listen on the port defined in the env
    port = int(os.getenv("PORT", 10000))  # Render defaults to 10000
    app.run(host="0.0.0.0", port=port)
