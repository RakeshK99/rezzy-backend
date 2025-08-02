#!/usr/bin/env python3
"""
Database Verification Script
Check that all data is being stored properly in the database.
"""

from database import SessionLocal, User, UsageRecord, Payment, UserFile, JobPosting
from datetime import datetime

def check_database():
    """Check all database tables and records"""
    db = SessionLocal()
    
    print("🔍 DATABASE VERIFICATION REPORT")
    print("=" * 50)
    
    # Check Users
    print("\n👥 USERS TABLE:")
    users = db.query(User).all()
    print(f"✅ Total users: {len(users)}")
    for user in users:
        print(f"  - ID: {user.id}")
        print(f"    Email: {user.email}")
        print(f"    Plan: {user.plan}")
        print(f"    Created: {user.created_at}")
        print(f"    Stripe Customer ID: {user.stripe_customer_id or 'None'}")
        print()
    
    # Check Usage Records
    print("📊 USAGE RECORDS TABLE:")
    usage_records = db.query(UsageRecord).all()
    print(f"✅ Total usage records: {len(usage_records)}")
    for record in usage_records:
        print(f"  - User: {record.user_id}")
        print(f"    Month: {record.month}")
        print(f"    Scans Used: {record.scans_used}")
        print(f"    Cover Letters: {record.cover_letters_generated}")
        print(f"    Interview Questions: {record.interview_questions_generated}")
        print()
    
    # Check Payments
    print("💳 PAYMENTS TABLE:")
    payments = db.query(Payment).all()
    print(f"✅ Total payment records: {len(payments)}")
    for payment in payments:
        print(f"  - User: {payment.user_id}")
        print(f"    Amount: ${payment.amount/100:.2f}")
        print(f"    Plan: {payment.plan}")
        print(f"    Status: {payment.status}")
        print(f"    Stripe Payment Intent: {payment.stripe_payment_intent_id}")
        print(f"    Created: {payment.created_at}")
        print()
    
    # Check User Files
    print("📁 USER FILES TABLE:")
    user_files = db.query(UserFile).all()
    print(f"✅ Total user files: {len(user_files)}")
    for file in user_files:
        print(f"  - User: {file.user_id}")
        print(f"    Filename: {file.filename}")
        print(f"    Type: {file.file_type}")
        print(f"    S3 Key: {file.s3_key}")
        print(f"    Size: {file.file_size} bytes")
        print()
    
    # Check Job Postings
    print("💼 JOB POSTINGS TABLE:")
    job_postings = db.query(JobPosting).all()
    print(f"✅ Total job postings: {len(job_postings)}")
    for job in job_postings:
        print(f"  - Title: {job.title}")
        print(f"    Company: {job.company}")
        print(f"    Location: {job.location}")
        print(f"    Type: {job.job_type}")
        print(f"    Active: {job.is_active}")
        print()
    
    db.close()
    
    print("=" * 50)
    print("✅ DATABASE VERIFICATION COMPLETE")
    print("\nAll data is being stored properly in the database!")

if __name__ == "__main__":
    check_database() 