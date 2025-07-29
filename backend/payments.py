# rezzy_app/backend/payments.py

from fastapi import APIRouter

router = APIRouter()

@router.post("/create-checkout-session")
async def create_checkout_session():
    # Your Stripe logic here
    return {"message": "Checkout session created"}

