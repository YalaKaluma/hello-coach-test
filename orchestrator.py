import os
import json
import yaml
from openai_helper import validate_response, generate_compliment
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime

app = Flask(__name__)
DATA_PATH = "data/users.json"
JOURNEY_PATH = "journeys/default.yaml"

# ✅ Create data folder and users.json if missing
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists(DATA_PATH):
    with open(DATA_PATH, "w") as f:
        json.dump({}, f)

# ✅ Load YAML journey steps
with open(JOURNEY_PATH, "r") as f:
    JOURNEY = yaml.safe_load(f)["journey"]

# ✅ Load/save user data
def load_data():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

# ✅ Get journey step by state
def get_step(state):
    return next((s for s in JOURNEY if s["state"] == state), None)

@app.route("/webhook", methods=["POST"])
def webhook():
    phone = request.values.get("From", "")
    message = request.values.get("Body", "").strip()
    now = datetime.now().isoformat()

    print(f"[{phone}] Incoming message: '{message}' at {now}")

    data = load_data()

    # Initialize new user
    if phone not in data:
        print(f"[{phone}] New user detected. Initializing profile.")
        data[phone] = {
            "start_date": now,
            "state": "intro",
            "day": 1,
            "profile": {},
            "responses": [],
            "conversation_log": []
        }

    user = data[phone]
    state = user.get("state", "intro")
    print(f"[{phone}] Current state: {state}")

    # 🔁 Reset command
    if message.lower() in ["reset", "/reset"]:
        print(f"[{phone}] Resetting user journey.")
        user["state"] = "intro"
        user["day"] = 1
        user["profile"] = {}
        user["conversation_log"] = []
        user["responses"] = []
        reply = "🔁 Your journey has been reset. Ready to start again? Type 'Next' to begin."

    # ⏭ Next command
    elif message.lower() == "next":
        user["day"] += 1
        user["state"] = f"day_{user['day']}_start"
        print(f"[{phone}] Moving to {user['state']}")
        reply = f"👣 Moving to day {user['day']}... Let’s go!"

    # 🧠 Normal conversation flow
    else:
        user["responses"].append({"timestamp": now, "message": message})
        print(f"[{phone}] Logged user message.")

        step = get_step(state)
        print(f"[{phone}] Matching step: {step['state'] if step else 'None'}")

        if step:
            is_valid = validate_response(state, message)
            print(f"[{phone}] GPT validation: {is_valid}")

            if is_valid:
                if "save_to" in step:
                    path = step["save_to"].split(".")
                    ref = user
                    for p in path[:-1]:
                        ref = ref.setdefault(p, {})
                    ref[path[-1]] = message
                    print(f"[{phone}] Saved message to {step['save_to']}")

                reply = step["message"]
                user["state"] = step.get("next_state", state)
                print(f"[{phone}] Transitioned to: {user['state']}")
            else:
                reply = "That’s a good start. Can you reflect a bit more deeply or give a more specific example?"
                print(f"[{phone}] Response rejected. Asking for deeper reflection.")
        else:
            reply = "I'm here to support you. Type 'Next' to continue your journey."
            print(f"[{phone}] No matching state. Sent fallback reply.")

    # 🟢 Add compliment if past 5 responses
    if len(user["responses"]) >= 5:
        compliment = generate_compliment(user)
        reply += f"\n\n🟢 Compliment of the day: {compliment}"
        print(f"[{phone}] Compliment added.")

    save_data(data)
    print(f"[{phone}] Data saved.")

    print(f"[{phone}] Final reply: {reply}\n{'-'*40}")
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
