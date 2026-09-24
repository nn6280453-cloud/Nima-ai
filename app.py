#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
from flask import Flask, request, jsonify, render_template

# ------------------------------------------------------------------
# Logging configuration – prints everything to stdout (Render shows it)
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,          # DEBUG gives you request/response dumps
    format="%(asctime)s | %(levelname)s | %(message)s",
)

app = Flask(__name__, template_folder="templates")

# ------------------------------------------------------------------
# 1️⃣  Load your OpenRouter API key
# ------------------------------------------------------------------
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    logging.error("OPENROUTER_API_KEY env var is missing!")
    # We’ll still start the server – the /ask route will fail gracefully
else:
    logging.debug(f"Using OpenRouter key: {API_KEY[:4]}…")

# ------------------------------------------------------------------
# 2️⃣  Front‑end
# ------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ------------------------------------------------------------------
# 3️⃣  /ask – the heart of the bot
# ------------------------------------------------------------------
@app.route("/ask", methods=["POST"])
def ask():
    try:
        # 3.1  Get the user message
        data = request.get_json(force=True)  # force=True -> even if no header
        if not data or "message" not in data:
            logging.warning("Malformed JSON or missing 'message'")
            return jsonify({"error": "Missing 'message' in request"}), 400

        user_input = data["message"].strip()
        if not user_input:
            logging.warning("Empty message received")
            return jsonify({"error": "Empty message"}), 400

        # 3.2  Build the OpenRouter payload
        payload = {
            "model": "deepseek/deepseek-r1",          # <-- change if you want a different model
            "messages": [
                {"role": "system", "content": "You are NIMA AI, a helpful cybersecurity assistant."},
                {"role": "user", "content": user_input},
            ],
            "max_tokens": 1024,
        }

        # 3.3  Set headers – Render requires a Referer
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://nima-ai-1t92.onrender.com",
        }

        logging.debug(f"Sending request to OpenRouter: {json.dumps(payload)[:200]}…")

        # 3.4  Call OpenRouter
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60,
        )
        r.raise_for_status()  # Will raise HTTPError for 4xx/5xx

        # 3.5  Parse the response – guard against unexpected shape
        resp_json = r.json()
        logging.debug(f"OpenRouter replied: {json.dumps(resp_json)[:200]}…")

        try:
            ai_reply = resp_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logging.exception("OpenRouter response missing 'choices[0].message.content'")
            return jsonify({"error": "Unexpected response structure from OpenRouter"}), 502

        return jsonify({"reply": ai_reply})

    except requests.exceptions.RequestException as e:
        # Network or HTTP error
        logging.exception("Request to OpenRouter failed")
        return jsonify({"error": f"Request failed: {str(e)}"}), 502

    except Exception as e:
        # Any other Python error
        logging.exception("Unhandled exception in /ask")
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


# ------------------------------------------------------------------
# 4️⃣  Optional: silence the /favicon.ico 404s
# ------------------------------------------------------------------
@app.route("/favicon.ico")
def favicon():
    return "", 204


# ------------------------------------------------------------------
# 5️⃣  Run the app
# ------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logging.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
