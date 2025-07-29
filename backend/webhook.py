# rezzy_app/backend/webhook.py

from fastapi import APIRouter, Request
import stripe
import os

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@router.post("/")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return {"status": "invalid payload"}
    except stripe.error.SignatureVerificationError:
        return {"status": "invalid signature"}

    if event["type"] == "checkout.session.completed":
        print("✅ Payment confirmed!")

    return {"status": "success"}
