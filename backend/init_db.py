#!/usr/bin/env python3
"""
Database Initialization Script
Creates all required tables in the database
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_database():
    """Initialize the database with all tables"""
    try:
        from database import Base, engine
        
        print("🔨 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Test the connection
        from database import SessionLocal
        db = SessionLocal()
        db.close()
        print("✅ Database connection test successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Initializing Rezzy Database...")
    init_database() 