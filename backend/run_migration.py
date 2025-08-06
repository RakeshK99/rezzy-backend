#!/usr/bin/env python3
"""
Simple script to run database migration in Railway
"""

import subprocess
import sys
import os

def run_migration():
    """Run the database migration"""
    try:
        print("🔄 Starting database migration...")
        
        # Run the migration script
        result = subprocess.run([
            sys.executable, 
            "backend/migrate_database.py"
        ], capture_output=True, text=True)
        
        print("Migration output:")
        print(result.stdout)
        
        if result.stderr:
            print("Migration errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Database migration completed successfully!")
            return True
        else:
            print(f"❌ Database migration failed with return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1) 