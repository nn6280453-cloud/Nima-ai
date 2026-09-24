from flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__, template_folder='templates')

# Get API Key from environment variable
API_KEY = os.environ.get("OPENROUTER_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    # 1. Get user input
    data = request.json
    user_input = data.get("message", "").strip()
    
    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    # 2. Prepare payload for OpenRouter
    # Using 'deepseek/deepseek-r1' as requested, but you can change this model ID
    payload = {
        "model": "deepseek/deepseek-r1", 
        "messages": [
            {"role": "system", "content": "You are NIMA AI, a helpful cybersecurity assistant."},
            {"role": "user", "content": user_input}
        ],
        "max_tokens": 1024
    }

    # 3. Set headers
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000", # Required by OpenRouter for free tier
        "X-Title": "NIMA AI Terminal"
    }

    try:
        # 4. Send request
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60
        )
        
        # Raise exception for bad status codes (e.g., 401 Unauthorized)
        r.raise_for_status()
        
        response_data = r.json()
        
        # 5. Extract the reply from the complex JSON structure
        try:
            ai_reply = response_data['choices'][0]['message']['content']
            return jsonify({"reply": ai_reply})
        except (KeyError, IndexError) as e:
            return jsonify({"error": "Invalid response format from API", "details": str(e)}), 500

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request failed: {str(e)}"}), 500

if __name__ == "__main__":
    # Run on port 5000 or the PORT env variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
