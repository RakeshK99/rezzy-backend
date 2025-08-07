#!/usr/bin/env python3
"""
Quick script to clear all user data from the database
Run this to reset the database for fresh testing
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clear_database():
    """Clear all user data from the database"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return False
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Get session
        db = SessionLocal()
        
        try:
            print("🗑️  Clearing all user data...")
            
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
            
            total_cleared = 0
            for table in tables_to_clear:
                try:
                    # Count and delete records
                    count_result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                    
                    if count > 0:
                        db.execute(text(f"DELETE FROM {table}"))
                        total_cleared += count
                        print(f"✅ Cleared {count} records from {table}")
                    else:
                        print(f"ℹ️  {table}: already empty")
                        
                except Exception as e:
                    print(f"⚠️  Warning: Could not clear {table}: {e}")
            
            # Commit the changes
            db.commit()
            print(f"✅ Successfully cleared {total_cleared} total records!")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing database: {e}")
            db.rollback()
            return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        return False

if __name__ == "__main__":
    print("🧹 Quick Database Clear")
    print("=" * 30)
    success = clear_database()
    if success:
        print("🎉 Database cleared! You can now create fresh accounts.")
    else:
        print("❌ Failed to clear database")
