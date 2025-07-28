import stripe
from dotenv import load_dotenv
import os

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(price_id):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='http://localhost:8501/success',
            cancel_url='http://localhost:8501/cancel',
        )
        return session.url
    except Exception as e:
        return str(e)
