import stripe
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Plan configurations
PLAN_PRICES = {
    "starter": {
        "price_id": os.getenv('STRIPE_STARTER_PRICE_ID'),
        "amount": 900,  # $9.00 in cents
        "currency": "usd"
    },
    "premium": {
        "price_id": os.getenv('STRIPE_PREMIUM_PRICE_ID'),
        "amount": 1900,  # $19.00 in cents
        "currency": "usd"
    }
}

class StripeService:
    def __init__(self):
        self.stripe = stripe
    
    def create_customer(self, email: str, user_id: str) -> Optional[str]:
        """Create a Stripe customer"""
        try:
            customer = self.stripe.Customer.create(
                email=email,
                metadata={
                    "user_id": user_id
                }
            )
            return customer.id
        except Exception as e:
            print(f"Error creating Stripe customer: {e}")
            return None
    
    def create_checkout_session(self, user_id: str, plan: str, success_url: str, cancel_url: str) -> Optional[str]:
        """Create a Stripe checkout session"""
        try:
            if plan not in PLAN_PRICES:
                raise ValueError(f"Invalid plan: {plan}")
            
            price_config = PLAN_PRICES[plan]
            
            session = self.stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_config['price_id'],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id,
                    "plan": plan
                }
            )
            
            return session.id
            
        except Exception as e:
            print(f"Error creating checkout session: {e}")
            return None
    
    def create_payment_intent(self, user_id: str, plan: str) -> Optional[Dict[str, Any]]:
        """Create a payment intent for one-time payments"""
        try:
            if plan not in PLAN_PRICES:
                raise ValueError(f"Invalid plan: {plan}")
            
            price_config = PLAN_PRICES[plan]
            
            intent = self.stripe.PaymentIntent.create(
                amount=price_config['amount'],
                currency=price_config['currency'],
                metadata={
                    "user_id": user_id,
                    "plan": plan
                }
            )
            
            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id
            }
            
        except Exception as e:
            print(f"Error creating payment intent: {e}")
            return None
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription details"""
        try:
            subscription = self.stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "plan": subscription.items.data[0].price.id if subscription.items.data else None,
                "current_period_end": subscription.current_period_end,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
        except Exception as e:
            print(f"Error retrieving subscription: {e}")
            return None
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription"""
        try:
            subscription = self.stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return subscription.status == 'active'
        except Exception as e:
            print(f"Error canceling subscription: {e}")
            return False
    
    def handle_webhook(self, payload: bytes, sig_header: str) -> Optional[Dict[str, Any]]:
        """Handle Stripe webhook events"""
        try:
            webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
            event = self.stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            return {
                "type": event['type'],
                "data": event['data']
            }
            
        except Exception as e:
            print(f"Error handling webhook: {e}")
            return None
    
    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer details"""
        try:
            customer = self.stripe.Customer.retrieve(customer_id)
            return {
                "id": customer.id,
                "email": customer.email,
                "metadata": customer.metadata
            }
        except Exception as e:
            print(f"Error retrieving customer: {e}")
            return None

# Global Stripe service instance
stripe_service = StripeService() 