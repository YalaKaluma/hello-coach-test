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

    data = load_data()

    # Initialize user if new
    if phone not in data:
        data[phone] = {"start_date": now, "responses": []}

    # Log this message
    data[phone]["responses"].append({"timestamp": now, "message": message})
    save_data(data)

    # Count how many messages the user has sent
    msg_count = len(data[phone]["responses"])

    # Select the response based on the message count
    if msg_count == 1:
        reply = ("Welcome! Let’s start your 28-day journey. "
                 "Today, tell me about the 3 happiest moments of your day.")
    elif msg_count == 2:
        reply = ("Great start! Now, what is one meaningful goal you want to achieve "
                 "in the next 6 months?")
    elif msg_count == 3:
        reply = ("Thanks for sharing. Next: What are your 3 biggest strengths, "
                 "and how can they help you achieve your goal?")
    elif msg_count == 4:
        reply = ("Amazing. Now let’s go deeper — what’s the biggest blocker, fear, "
                 "or constraint standing in your way?")
    else:
        reply = "You're doing great. Keep going — I believe in you. 🌟"

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
