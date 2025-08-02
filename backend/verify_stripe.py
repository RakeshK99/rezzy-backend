#!/usr/bin/env python3
"""
Stripe Payment Verification Script
Verify that payments will be properly sent to your Stripe account.
"""

import stripe
import os
from dotenv import load_dotenv

def verify_stripe_setup():
    """Verify Stripe configuration and account setup"""
    load_dotenv()
    
    print("💳 STRIPE PAYMENT VERIFICATION")
    print("=" * 50)
    
    # Check API Key
    stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe_secret_key:
        print("❌ STRIPE_SECRET_KEY not found in .env file")
        return False
    
    print(f"✅ Stripe Secret Key: {stripe_secret_key[:20]}...")
    stripe.api_key = stripe_secret_key
    
    # Check Account Information
    try:
        account = stripe.Account.retrieve()
        print(f"\n🏦 STRIPE ACCOUNT:")
        print(f"  Account ID: {account.id}")
        print(f"  Business Type: {account.business_type or 'Individual'}")
        print(f"  Country: {account.country}")
        print(f"  Default Currency: {account.default_currency}")
        print(f"  Charges Enabled: {'✅ Yes' if account.charges_enabled else '❌ No'}")
        print(f"  Payouts Enabled: {'✅ Yes' if account.payouts_enabled else '❌ No'}")
        
        if not account.charges_enabled:
            print("\n⚠️  WARNING: Charges are not enabled on your Stripe account!")
            print("   You need to complete your Stripe account setup to receive payments.")
            print("   Go to: https://dashboard.stripe.com/account/onboarding")
        
        if not account.payouts_enabled:
            print("\n⚠️  WARNING: Payouts are not enabled on your Stripe account!")
            print("   You need to complete payout setup to receive money.")
            print("   Go to: https://dashboard.stripe.com/account/payouts")
        
    except Exception as e:
        print(f"❌ Error retrieving account info: {e}")
        return False
    
    # Check Price IDs
    print(f"\n💰 PRICE CONFIGURATION:")
    price_ids = {
        'starter': os.getenv('STRIPE_STARTER_PRICE_ID'),
        'premium': os.getenv('STRIPE_PREMIUM_PRICE_ID'),
        'elite': os.getenv('STRIPE_ELITE_PRICE_ID')
    }
    
    for plan, price_id in price_ids.items():
        if price_id:
            try:
                price = stripe.Price.retrieve(price_id)
                print(f"  ✅ {plan.capitalize()}: ${price.unit_amount/100:.2f} {price.currency}")
                print(f"     Price ID: {price.id}")
                print(f"     Active: {'✅ Yes' if price.active else '❌ No'}")
            except Exception as e:
                print(f"  ❌ {plan.capitalize()}: Invalid price ID - {e}")
        else:
            print(f"  ❌ {plan.capitalize()}: Price ID not set")
    
    # Check Webhook Configuration
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    if webhook_secret:
        print(f"\n🔗 WEBHOOK CONFIGURATION:")
        print(f"  ✅ Webhook Secret: {webhook_secret[:20]}...")
    else:
        print(f"\n❌ STRIPE_WEBHOOK_SECRET not found")
    
    # Test Payment Flow
    print(f"\n🧪 PAYMENT FLOW TEST:")
    try:
        # Test creating a checkout session
        from stripe_service import StripeService
        stripe_service = StripeService()
        
        session_id = stripe_service.create_checkout_session(
            user_id="test_verification",
            plan="starter",
            success_url="http://localhost:3000/success",
            cancel_url="http://localhost:3000/cancel"
        )
        
        if session_id:
            print(f"  ✅ Checkout session created successfully")
            print(f"     Session ID: {session_id}")
            
            # Get session details
            session = stripe.checkout.Session.retrieve(session_id)
            print(f"     Amount: ${session.amount_total/100:.2f}")
            print(f"     Currency: {session.currency}")
            print(f"     Status: {session.status}")
        else:
            print(f"  ❌ Failed to create checkout session")
            
    except Exception as e:
        print(f"  ❌ Payment flow test failed: {e}")
    
    print(f"\n" + "=" * 50)
    
    if account.charges_enabled and account.payouts_enabled:
        print("✅ STRIPE SETUP COMPLETE - Payments will go to your account!")
        print("\n💰 When users pay:")
        print("  1. Money goes directly to your Stripe account")
        print("  2. You can see payments in your Stripe Dashboard")
        print("  3. Payouts will be sent to your bank account")
        print("  4. All transaction fees are automatically deducted")
    else:
        print("❌ STRIPE SETUP INCOMPLETE - Complete account setup first!")
        print("\n📋 Next steps:")
        print("  1. Complete Stripe account verification")
        print("  2. Enable charges and payouts")
        print("  3. Add bank account for payouts")
        print("  4. Test with a small payment")
    
    return account.charges_enabled and account.payouts_enabled

if __name__ == "__main__":
    verify_stripe_setup() 