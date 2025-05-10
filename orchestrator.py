from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    resp = MessagingResponse()
    msg = resp.message("Hello! You're talking to your future WhatsApp coach.")
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)