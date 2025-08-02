#!/usr/bin/env python3
"""
Database Update Script for Rezzy
Adds the new ResumeAnalysis table to existing database
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Base, engine

def update_database():
    """Add new tables to existing database"""
    print("🔧 Updating database schema...")
    
    try:
        # Create new tables (this will only create tables that don't exist)
        Base.metadata.create_all(bind=engine)
        print("✅ Database schema updated successfully!")
        print("📋 New tables added:")
        print("   - resume_analyses (for storing analysis results)")
        
        return True
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        return False

if __name__ == "__main__":
    load_dotenv()
    update_database() 