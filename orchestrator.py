import os
import json
import yaml
import logging
from openai_helper import validate_response, generate_compliment
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
from openai_helper import validate_response, generate_compliment, generate_followup

app = Flask(__name__)
DATA_PATH = "data/users.json"
JOURNEY_PATH = "journeys/default.yaml"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    logger.info(f"[{phone}] Incoming message: '{message}' at {now}")

    data = load_data()

    # Initialize new user
    if phone not in data:
        logger.info(f"[{phone}] New user detected. Initializing profile.")
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
    logger.info(f"[{phone}] Current state: {state}")

    # 🔁 Reset command
    if message.lower() in ["reset", "/reset"]:
        logger.info(f"[{phone}] Resetting user journey.")
        user["state"] = "intro"
        user["day"] = 1
        user["profile"] = {}
        user["conversation_log"] = []
        user["responses"] = []
        reply = "🔁 Your journey has been reset. Ready to start again? Type 'Next' to begin."

    # ⏭ Next command (smart state-aware logic)
    elif message.lower() == "next":
        if state == "intro":
            user["state"] = "waiting_for_happy"
            reply = "Let’s begin. Tell me about a happy moment from your day."
            logger.info(f"[{phone}] Transitioning from intro → waiting_for_happy")
        elif state == "waiting_for_blocker":
            user["day"] += 1
            user["state"] = f"day_{user['day']}_start"
            reply = f"👣 Great! Starting Day {user['day']}."
            logger.info(f"[{phone}] Transitioning from blocker → {user['state']}")
        else:
            reply = "Let’s keep going. I’m here to help — tell me more."
            logger.info(f"[{phone}] 'Next' received but no transition. Staying in {user['state']}")

    # 🧠 Normal conversation flow
    else:
        user["responses"].append({"timestamp": now, "message": message})
        logger.info(f"[{phone}] Logged user message.")

        step = get_step(state)
        logger.info(f"[{phone}] Matching step: {step['state'] if step else 'None'}")

#        if step:
#            is_valid = validate_response(state, message)
#            logger.info(f"[{phone}] GPT validation: {is_valid}")

        if step:
            recent_history = user["responses"][-5:]
            context = "\n".join([f"- {r['message']}" for r in recent_history])
            is_valid = validate_response(state, message, context)
            logger.info(f"[{phone}] GPT validation: {is_valid}")
                     

            if is_valid:
                if "save_to" in step:
                    path = step["save_to"].split(".")
                    ref = user
                    for p in path[:-1]:
                        ref = ref.setdefault(p, {})
                    ref[path[-1]] = message
                    logger.info(f"[{phone}] Saved message to {step['save_to']}")

                reply = step["message"]
                user["state"] = step.get("next_state", state)
                logger.info(f"[{phone}] Transitioned to: {user['state']}")
            else:
                #reply = "That’s a good start. Can you reflect a bit more deeply or give a more specific example?"
                #logger.info(f"[{phone}] Response rejected. Asking for deeper reflection.")
                #reply = generate_followup(state, message)
                #logger.info(f"[{phone}] Response rejected. Sent AI follow-up: {reply}")

                reply = generate_followup(state, message, context)
#                logger.info(f"[{phone}] No matching step. Sent fallback follow-up: {reply}")
                logger.info(f"[{phone}] Response rejected. Sent follow-up: {reply}")
        
        else:
            #reply = "I'm here to support you. Type 'Next' to continue your journey."
            #logger.info(f"[{phone}] No matching state. Sent fallback reply.")
            #reply = generate_followup(state, message)
            #logger.info(f"[{phone}] Response rejected. Sent AI follow-up: {reply}")

            reply = generate_followup(state, message, context)
#            logger.info(f"[{phone}] No matching step. Sent fallback follow-up: {reply}")
            logger.info(f"[{phone}] Response rejected. Sent follow-up: {reply}")

    


    # 🟢 Add compliment only when day has just started
    if message.lower() == "next" and user["state"].startswith("day_"):
        compliment = generate_compliment(user)
        reply += f"\n\n🟢 Compliment of the day: {compliment}"
        logger.info(f"[{phone}] Compliment added.")
    
    
    save_data(data)
    logger.info(f"[{phone}] Data saved.")

    logger.info(f"[{phone}] Final reply: {reply}\n{'-'*40}")
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
