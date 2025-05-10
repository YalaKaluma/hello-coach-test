# openai_helper.py

import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_compliment(user_data):
    recent_messages = user_data.get("responses", [])[-5:]  # last 5 entries
    text = "\n".join([f"- {entry['message']}" for entry in recent_messages])

    prompt = (
        "You are a kind and supportive coach. Based on these recent reflections:\n"
        f"{text}\n\n"
        "Write a warm, personal compliment that highlights the user's strengths or effort."
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50,
        temperature=0.8
    )

    return response.choices[0].message.content.strip()
