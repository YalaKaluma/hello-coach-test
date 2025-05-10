import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

def generate_compliment(user_data):
    recent_messages = user_data.get("responses", [])[-5:]
    text = "\n".join([f"- {entry['message']}" for entry in recent_messages])

    prompt = (
        "You are a kind and supportive coach. Based on these recent reflections:\n"
        f"{text}\n\n"
        "Write a warm, personal compliment that highlights the user's strengths or effort."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50,
        temperature=0.8
    )

    return response.choices[0].message.content.strip()

def validate_response(state, message, context=""):
    prompt = (
        f"You are a coach reviewing a user's reflection.\n\n"
        f"State: {state}\n"
        f"Recent context:\n{context}\n"
        f"User input: \"{message}\"\n\n"
        f"Is this a sufficiently thoughtful and specific response to move on?\n"
        f"Answer only YES or NO."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3,
        temperature=0
    )

    answer = response.choices[0].message.content.strip().lower()
    return "yes" in answer

def generate_followup(state, user_message, context=""):
    prompt = (
        "You are a thoughtful and supportive coach.\n\n"
        f"The user is currently at the step: \"{state}\".\n"
        "This step requires a thoughtful and specific answer to move on.\n\n"
        f"The user said: \"{user_message}\"\n"
        f"Recent context:\n{context}\n\n"
        "This is too shallow or vague to proceed.\n"
        "Write a gentle and personalized follow-up question to help them dig deeper or clarify their response."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60,
        temperature=0.8
    )

    return response.choices[0].message.content.strip()
