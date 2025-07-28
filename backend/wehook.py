# backend/webhook.py
import stripe
from fastapi import FastAPI, Request

app = FastAPI()
endpoint_secret = "your_webhook_secret"

@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        return {"status": "invalid"}

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # mark user as subscribed (use user_email or metadata)
    return {"status": "success"}
