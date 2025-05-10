import os
import json
import yaml
from openai_helper import generate_compliment
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
    JOURNEY = yaml.safe_load(f)["journey"]


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


def get_step(state):
    for step in JOURNEY:
        if step["state"] == state:
            return step
    return None



@app.route("/webhook", methods=["POST"])
def webhook():
    phone = request.values.get("From", "")
    message = request.values.get("Body", "").strip()
    now = datetime.now().isoformat()

    data = load_data()

    # ✅ Initialize user if needed
    if phone not in data:
        data[phone] = {
            "start_date": now,
            "state": "intro",
            "day": 1,
            "profile": {},
            "responses": []
        }

    user = data[phone]
    state = user.get("state", "intro")

    # ✅ Handle "Next" for testing
    if message.lower() == "next":
        user["day"] += 1
        user["state"] = f"day_{user['day']}_start"
        reply = f"👣 Moving to day {user['day']}... Let’s go!"

    else:
        # ✅ Save user response
        user["responses"].append({"timestamp": now, "message": message})

        # ✅ Look up current step in YAML
        step = next((s for s in JOURNEY if s["state"] == state), None)

        if step:
            # If step specifies where to store the input (e.g., goal, strengths, etc.)
            if "save_to" in step:
                path = step["save_to"].split(".")
                ref = user
                for p in path[:-1]:
                    ref = ref.setdefault(p, {})
                ref[path[-1]] = message

            reply = step["message"]
            user["state"] = step.get("next_state", state)

        else:
            reply = "I'm here to support you. Type 'Next' to continue your journey."

    # ✅ Add compliment if enough responses
    if len(user["responses"]) >= 5:
        compliment = generate_compliment(user)
        reply += f"\n\n🟢 Compliment of the day: {compliment}"

    save_data(data)

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
