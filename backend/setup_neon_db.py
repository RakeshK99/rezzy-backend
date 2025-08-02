#!/usr/bin/env python3
"""
NeonDB Setup Script for Rezzy
This script helps you set up and test your NeonDB connection.
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine, text

def test_connection():
    """Test the database connection"""
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in .env file")
        return False
    
    print("🔍 Testing database connection...")
    
    try:
        # Test with psycopg2
        conn = psycopg2.connect(database_url)
        print("✅ psycopg2 connection successful")
        conn.close()
        
        # Test with SQLAlchemy
        engine_test = create_engine(database_url)
        with engine_test.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ SQLAlchemy connection successful")
            print(f"📊 Database version: {version}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def create_tables():
    """Create all database tables"""
    print("🔨 Creating database tables...")
    
    try:
        from database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def setup_neon_instructions():
    """Print instructions for setting up NeonDB"""
    print("\n" + "="*60)
    print("🚀 NEONDB SETUP INSTRUCTIONS")
    print("="*60)
    print("1. Go to https://console.neon.tech/")
    print("2. Sign up/Login and create a new project")
    print("3. Choose a project name (e.g., 'rezzy')")
    print("4. Select a region (us-east-1 recommended)")
    print("5. Copy the connection string from the dashboard")
    print("6. Update your .env file with the DATABASE_URL")
    print("7. Run this script again to test the connection")
    print("\nExample DATABASE_URL format:")
    print("DATABASE_URL=postgresql://username:password@ep-example-123456.us-east-1.aws.neon.tech/rezzy_db?sslmode=require")
    print("="*60)

def create_env_template():
    """Create .env file from template if it doesn't exist"""
    if not os.path.exists(".env"):
        print("📝 Creating .env file from template...")
        if os.path.exists("env_template.txt"):
            import shutil
            shutil.copy("env_template.txt", ".env")
            print("✅ .env file created from template")
            print("⚠️  Please edit .env file with your actual API keys")
            return True
        else:
            print("❌ env_template.txt not found")
            return False
    return True

def main():
    """Main setup function"""
    print("🎯 Rezzy NeonDB Setup")
    print("="*40)
    
    # Create .env file if it doesn't exist
    if not create_env_template():
        setup_neon_instructions()
        return
    
    # Test connection
    if test_connection():
        print("\n🎉 Database connection successful!")
        
        # Create tables
        if create_tables():
            print("\n✅ Setup complete! Your NeonDB is ready for Rezzy.")
            print("\nNext steps:")
            print("1. Start your backend server")
            print("2. Test the API endpoints")
            print("3. Deploy to production")
        else:
            print("\n❌ Failed to create tables")
    else:
        print("\n❌ Database connection failed")
        setup_neon_instructions()

if __name__ == "__main__":
    main() 