import os
import json
import yaml
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime


app = Flask(__name__)
DATA_PATH = "data/users.json"
JOURNEY_PATH = "journeys/default.yaml"



# ✅ Create data folder and users.json file if missing
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists(DATA_PATH):
    with open(DATA_PATH, "w") as f:
        json.dump({}, f)

# Load journey steps on startup
with open(JOURNEY_PATH, "r") as f:
    JOURNEY = yaml.safe_load(f)["steps"]


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

    data = load_data()

    # Initialize user if new
    if phone not in data:
        data[phone] = {"start_date": now, "responses": []}

    # Log this message
    data[phone]["responses"].append({"timestamp": now, "message": message})
    save_data(data)

    # Count how many messages the user has sent
    msg_count = len(data[phone]["responses"])

    # Use YAML journey steps based on message count
    reply = "You're doing great. Keep going — I believe in you. 🌟"
    for step in JOURNEY:
        if step["trigger"] == msg_count:
            reply = step["message"]
            break

    if msg_count >= 5:
        compliment = generate_compliment(data[phone])
        reply += f"\n\n🟢 Compliment of the day: {compliment}"


    # Send back the reply
    resp = MessagingResponse()
    resp.message(reply)
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
