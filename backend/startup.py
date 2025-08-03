#!/usr/bin/env python3
"""
Startup script for Railway deployment
Handles database initialization and graceful startup
"""

import os
import time
import sys
from sqlalchemy import create_engine, text
from database import DATABASE_URL

def wait_for_database(max_retries=30, delay=2):
    """Wait for database to be available"""
    print("Waiting for database connection...")
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
        except Exception as e:
            print(f"❌ Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    print("❌ Database connection failed after all attempts")
    return False

def main():
    """Main startup function"""
    print("🚀 Starting Rezzy API...")
    
    # Check if we're in production
    if os.getenv("ENVIRONMENT") == "production":
        print("📦 Production environment detected")
        
        # Wait for database
        if not wait_for_database():
            print("❌ Failed to connect to database, exiting...")
            sys.exit(1)
    
    print("✅ Startup checks completed successfully!")
    print("🎯 Starting FastAPI application...")

if __name__ == "__main__":
    main() 