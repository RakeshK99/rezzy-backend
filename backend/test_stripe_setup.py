#!/usr/bin/env python3
"""
Stripe Setup Test Script
Tests Stripe configuration and payment flow
"""

import os
import stripe
from dotenv import load_dotenv

load_dotenv()

def test_stripe_config():
    """Test Stripe configuration"""
    print("🔍 Testing Stripe Configuration...")
    
    # Check if Stripe key is set
    stripe_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe_key:
        print("❌ STRIPE_SECRET_KEY not found")
        return False
    
    if stripe_key.startswith('sk_test_'):
        print("⚠️  Using TEST mode - switch to LIVE keys for production")
    elif stripe_key.startswith('sk_live_'):
        print("✅ Using LIVE mode - ready for real payments")
    else:
        print("❌ Invalid Stripe key format")
        return False
    
    # Test Stripe connection
    try:
        stripe.api_key = stripe_key
        account = stripe.Account.retrieve()
        print(f"✅ Connected to Stripe account: {account.business_profile.name}")
        return True
    except Exception as e:
        print(f"❌ Stripe connection failed: {e}")
        return False

def test_price_ids():
    """Test if price IDs are configured"""
    print("\n🔍 Testing Price IDs...")
    
    starter_price = os.getenv('STRIPE_STARTER_PRICE_ID')
    premium_price = os.getenv('STRIPE_PREMIUM_PRICE_ID')
    
    if not starter_price:
        print("❌ STRIPE_STARTER_PRICE_ID not found")
        return False
    
    if not premium_price:
        print("❌ STRIPE_PREMIUM_PRICE_ID not found")
        return False
    
    print(f"✅ Starter Price ID: {starter_price}")
    print(f"✅ Premium Price ID: {premium_price}")
    
    # Test if prices exist in Stripe
    try:
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        starter = stripe.Price.retrieve(starter_price)
        premium = stripe.Price.retrieve(premium_price)
        print(f"✅ Starter Price: ${starter.unit_amount/100}/month")
        print(f"✅ Premium Price: ${premium.unit_amount/100}/month")
        return True
    except Exception as e:
        print(f"❌ Price validation failed: {e}")
        return False

def test_webhook_secret():
    """Test webhook secret"""
    print("\n🔍 Testing Webhook Secret...")
    
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    if not webhook_secret:
        print("❌ STRIPE_WEBHOOK_SECRET not found")
        return False
    
    if webhook_secret.startswith('whsec_'):
        print("✅ Webhook secret configured")
        return True
    else:
        print("❌ Invalid webhook secret format")
        return False

def test_checkout_session():
    """Test creating a checkout session"""
    print("\n🔍 Testing Checkout Session Creation...")
    
    try:
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        starter_price = os.getenv('STRIPE_STARTER_PRICE_ID')
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': starter_price,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://end-seven.vercel.app/dashboard?success=true',
            cancel_url='https://end-seven.vercel.app/dashboard?canceled=true',
            metadata={
                "user_id": "test123",
                "plan": "starter"
            }
        )
        
        print(f"✅ Checkout session created: {session.id}")
        print(f"✅ Checkout URL: {session.url}")
        return True
        
    except Exception as e:
        print(f"❌ Checkout session creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🎯 Stripe Setup Test")
    print("=" * 40)
    
    tests = [
        test_stripe_config,
        test_price_ids,
        test_webhook_secret,
        test_checkout_session
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Stripe is configured correctly.")
        print("\n💰 Next steps:")
        print("1. Add environment variables to Railway")
        print("2. Test payment flow in your app")
        print("3. Monitor payments in Stripe Dashboard")
    else:
        print("❌ Some tests failed. Please fix the issues above.")

if __name__ == "__main__":
    main() 