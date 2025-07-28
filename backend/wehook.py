import stripe
from fastapi import FastAPI, Request
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # Or hardcode for testing

app = FastAPI()

@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")  # or hardcode

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return {"status": "invalid payload"}
    except stripe.error.SignatureVerificationError as e:
        return {"status": "invalid signature"}

    if event["type"] == "checkout.session.completed":
        print("✅ Payment confirmed!")
        # Add logic to update session state, DB, etc.

    return {"status": "success"}
