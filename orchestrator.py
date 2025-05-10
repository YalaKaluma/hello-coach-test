import os
import json
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime

app = Flask(__name__)
DATA_PATH = "data/users.json"

# ✅ Create data folder and users.json file if missing
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists(DATA_PATH):
    with open(DATA_PATH, "w") as f:
        json.dump({}, f)



# Load user data from file
def load_data():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)

# Save user data to file
def save_data(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/webhook", methods=["POST"])
def webhook():
    phone = request.values.get("From", "")
    message = request.values.get("Body", "").strip()
    now = datetime.now().isoformat()

    # Load and update data
    data = load_data()
    if phone not in data:
        data[phone] = {"start_date": now, "responses": []}
    data[phone]["responses"].append({"timestamp": now, "message": message})
    save_data(data)

    # Respond with confirmation
    resp = MessagingResponse()
    resp.message("Thanks for your message. It's been recorded.")
    return str(resp)

@app.route("/debug", methods=["GET"])
def debug():
    try:
        with open(DATA_PATH, "r") as f:
            data = json.load(f)
        return f"<pre>{json.dumps(data, indent=2)}</pre>"
    except Exception as e:
        return f"Error reading data: {e}", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
