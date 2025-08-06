#!/usr/bin/env python3
"""
Database Migration Script for Rezzy
Adds new user profile fields: middle_name, position_level, job_category, current_resume_id
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate_database():
    """Migrate database to add new user profile fields"""
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return False
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("🔍 Checking current database schema...")
            
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name IN ('middle_name', 'position_level', 'job_category', 'current_resume_id')
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            print(f"Existing columns: {existing_columns}")
            
            # Add missing columns
            migrations = []
            
            if 'middle_name' not in existing_columns:
                migrations.append("""
                    ALTER TABLE users 
                    ADD COLUMN middle_name VARCHAR
                """)
                print("➕ Will add middle_name column")
            
            if 'position_level' not in existing_columns:
                migrations.append("""
                    ALTER TABLE users 
                    ADD COLUMN position_level VARCHAR
                """)
                print("➕ Will add position_level column")
            
            if 'job_category' not in existing_columns:
                migrations.append("""
                    ALTER TABLE users 
                    ADD COLUMN job_category VARCHAR
                """)
                print("➕ Will add job_category column")
            
            if 'current_resume_id' not in existing_columns:
                migrations.append("""
                    ALTER TABLE users 
                    ADD COLUMN current_resume_id INTEGER REFERENCES user_files(id)
                """)
                print("➕ Will add current_resume_id column")
            
            # Execute migrations
            if migrations:
                print(f"\n🚀 Executing {len(migrations)} migrations...")
                for i, migration in enumerate(migrations, 1):
                    print(f"Migration {i}/{len(migrations)}: {migration.strip()}")
                    conn.execute(text(migration))
                
                conn.commit()
                print("✅ Database migration completed successfully!")
            else:
                print("✅ Database is already up to date!")
            
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Starting Rezzy database migration...")
    success = migrate_database()
    if success:
        print("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("💥 Migration failed!")
        sys.exit(1) 