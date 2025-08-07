#!/usr/bin/env python3
"""
Script to clear only existing tables in the database
"""

import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clear_existing_tables():
    """Clear only tables that exist in the database"""
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
            print("🔍 Checking existing tables...")
            
            # Get list of existing tables
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            print(f"📋 Found {len(existing_tables)} tables: {', '.join(existing_tables)}")
            
            # Tables to clear (in order of dependencies)
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
            
            # Only clear tables that exist
            existing_tables_to_clear = [table for table in tables_to_clear if table in existing_tables]
            
            print(f"🗑️  Clearing {len(existing_tables_to_clear)} existing tables...")
            
            total_cleared = 0
            for table in existing_tables_to_clear:
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
                    db.rollback()
                    db = SessionLocal()  # Get fresh session
            
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
    print("🧹 Clear Existing Tables")
    print("=" * 30)
    success = clear_existing_tables()
    if success:
        print("🎉 Database cleared! You can now create fresh accounts.")
    else:
        print("❌ Failed to clear database")
