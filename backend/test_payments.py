#!/usr/bin/env python3
"""
Payment Testing Script for Rezzy
This script tests all payment-related functionality including Stripe integration.
"""

import os
import stripe
from dotenv import load_dotenv
from stripe_service import PLAN_PRICES, StripeService

def test_stripe_configuration():
    """Test Stripe configuration"""
    load_dotenv()
    
    stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_secret_key:
        print("❌ STRIPE_SECRET_KEY not found in .env file")
        return False
    
    try:
        stripe.api_key = stripe_secret_key
        # Test Stripe connection by listing customers
        customers = stripe.Customer.list(limit=1)
        print("✅ Stripe connection successful")
        return True
    except Exception as e:
        print(f"❌ Stripe connection failed: {e}")
        return False

def test_plan_prices():
    """Test plan prices configuration"""
    print("\n📊 Testing Plan Prices:")
    for plan, price_info in PLAN_PRICES.items():
        print(f"  {plan.capitalize()}: ${price_info['amount']/100:.2f} (ID: {price_info['price_id']})")
    
    # Verify price IDs exist in Stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    for plan, price_info in PLAN_PRICES.items():
        try:
            price = stripe.Price.retrieve(price_info['price_id'])
            print(f"✅ {plan.capitalize()} price ID verified")
        except Exception as e:
            print(f"❌ {plan.capitalize()} price ID invalid: {e}")

def test_checkout_session():
    """Test checkout session creation"""
    print("\n🛒 Testing Checkout Session Creation:")
    
    try:
        stripe_service = StripeService()
        session_id = stripe_service.create_checkout_session(
            user_id="test_user_123",
            plan="starter",
            success_url="http://localhost:3000/success",
            cancel_url="http://localhost:3000/cancel"
        )
        if session_id:
            print(f"✅ Checkout session created: {session_id}")
            return True
        else:
            print("❌ Failed to create checkout session")
            return False
    except Exception as e:
        print(f"❌ Checkout session creation failed: {e}")
        return False

def test_stripe_customer_creation():
    """Test Stripe customer creation"""
    print("\n👤 Testing Stripe Customer Creation:")
    
    try:
        stripe_service = StripeService()
        customer_id = stripe_service.create_customer(
            email="test@example.com",
            user_id="test_user_123"
        )
        if customer_id:
            print(f"✅ Stripe customer created: {customer_id}")
            return True
        else:
            print("❌ Failed to create Stripe customer")
            return False
    except Exception as e:
        print(f"❌ Stripe customer creation failed: {e}")
        return False

def main():
    """Main testing function"""
    print("💳 Rezzy Payment System Test")
    print("="*40)
    
    # Test Stripe configuration
    if not test_stripe_configuration():
        print("\n❌ Stripe configuration failed. Please check your STRIPE_SECRET_KEY")
        return
    
    # Test plan prices
    test_plan_prices()
    
    # Test checkout session
    test_checkout_session()
    
    # Test customer creation
    test_stripe_customer_creation()
    
    print("\n🎉 Payment system test completed!")
    print("\nNext steps:")
    print("1. Test the full API endpoints")
    print("2. Test frontend integration")
    print("3. Deploy to production")

if __name__ == "__main__":
    main() 