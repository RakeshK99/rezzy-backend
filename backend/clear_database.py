#!/usr/bin/env python3
"""
Script to clear all user data from the database
This will remove all users and their associated data
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable not found!")
    sys.exit(1)

def clear_database():
    """Clear all user data from the database"""
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        print("🔍 Connecting to database...")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # Get session
        db = SessionLocal()
        
        try:
            print("🗑️  Clearing database tables...")
            
            # Clear tables in order (respecting foreign key constraints)
            tables_to_clear = [
                "interview_preparations",
                "optimized_resumes", 
                "resume_analyses",
                "job_applications",
                "payments",
                "usage_records",
                "user_files",
                "users"
            ]
            
            for table in tables_to_clear:
                try:
                    # Count records before deletion
                    count_result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                    
                    # Delete all records
                    db.execute(text(f"DELETE FROM {table}"))
                    
                    print(f"✅ Cleared {count} records from {table}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not clear {table}: {e}")
            
            # Commit the changes
            db.commit()
            print("✅ All user data cleared successfully!")
            
            # Verify tables are empty
            print("\n📊 Verification - Record counts:")
            for table in tables_to_clear:
                try:
                    count_result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                    print(f"   {table}: {count} records")
                except Exception as e:
                    print(f"   {table}: Error checking count - {e}")
            
        except Exception as e:
            print(f"❌ Error clearing database: {e}")
            db.rollback()
            raise
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        sys.exit(1)

def main():
    """Main function"""
    print("🧹 Rezzy Database Cleaner")
    print("=" * 40)
    print(f"Database URL: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else f"Database URL: {DATABASE_URL}")
    print()
    
    # Confirm before proceeding
    response = input("⚠️  This will DELETE ALL USER DATA. Are you sure? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Operation cancelled")
        sys.exit(0)
    
    print()
    clear_database()
    print()
    print("🎉 Database cleared successfully!")
    print("You can now create fresh accounts.")

if __name__ == "__main__":
    main()
