#!/usr/bin/env python3
"""
Environment variable checker for Railway deployment
"""

import os

def check_required_env_vars():
    """Check if all required environment variables are set"""
    required_vars = [
        "OPENAI_API_KEY",
        "DATABASE_URL", 
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
        "AWS_S3_BUCKET_NAME",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_STARTER_PRICE_ID",
        "STRIPE_PREMIUM_PRICE_ID"
    ]
    
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

if __name__ == "__main__":
    check_required_env_vars() 