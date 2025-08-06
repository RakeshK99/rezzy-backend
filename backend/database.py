from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import QueuePool
from datetime import datetime
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Database configuration optimized for NeonDB
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rezzy.db")

# Enhanced engine configuration for NeonDB scalability
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Additional connections that can be created
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)  # Clerk user ID
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    middle_name = Column(String, nullable=True)  # New field for middle name
    last_name = Column(String)
    plan = Column(String, default="free")  # free, starter, premium, elite
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    stripe_customer_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Profile fields
    position_level = Column(String, nullable=True)  # intern, junior, mid, senior, staff, etc.
    job_category = Column(String, nullable=True)  # swe, data_engineering, machine_learning, etc.
    current_resume_id = Column(Integer, ForeignKey("user_files.id"), nullable=True)  # Current active resume

class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    month = Column(String)  # Format: YYYY-MM
    scans_used = Column(Integer, default=0)
    cover_letters_generated = Column(Integer, default=0)
    interview_questions_generated = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserFile(Base):
    __tablename__ = "user_files"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    filename = Column(String)
    original_filename = Column(String)
    file_type = Column(String)  # resume, cover_letter, etc.
    s3_key = Column(String)  # AWS S3 object key
    file_size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    stripe_payment_intent_id = Column(String, unique=True)
    amount = Column(Integer)  # Amount in cents
    currency = Column(String, default="usd")
    plan = Column(String)
    status = Column(String)  # succeeded, failed, pending
    created_at = Column(DateTime, default=datetime.utcnow)

class JobPosting(Base):
    __tablename__ = "job_postings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    company = Column(String)
    location = Column(String)
    description = Column(Text)
    requirements = Column(Text)
    salary_range = Column(String, nullable=True)
    job_type = Column(String)  # full-time, part-time, contract, etc.
    experience_level = Column(String)  # entry, mid, senior
    source = Column(String)  # linkedin, indeed, etc.
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class JobApplication(Base):
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    job_title = Column(String)
    company = Column(String)
    location = Column(String, nullable=True)
    job_url = Column(String, nullable=True)
    application_status = Column(String, default="applied")  # applied, phone_screen, onsite, offer, rejected
    application_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Job details for optimization
    job_description = Column(Text, nullable=True)
    optimized_resume_id = Column(Integer, ForeignKey("user_files.id"), nullable=True)
    match_score = Column(Float, nullable=True)

class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    resume_file_id = Column(Integer, ForeignKey("user_files.id", ondelete="CASCADE"), nullable=True)
    resume_text = Column(Text)
    job_description = Column(Text)
    ai_evaluation = Column(Text)  # JSON string of AI evaluation results
    keyword_gaps = Column(Text)   # JSON string of keyword gaps
    job_analysis = Column(Text)   # JSON string of job analysis
    created_at = Column(DateTime, default=datetime.utcnow)

class OptimizedResume(Base):
    __tablename__ = "optimized_resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    original_resume_id = Column(Integer, ForeignKey("user_files.id", ondelete="CASCADE"))
    job_posting_id = Column(Integer, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=True)
    job_title = Column(String)
    company = Column(String)
    optimized_content = Column(Text)
    optimization_notes = Column(Text, nullable=True)
    match_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class InterviewPreparation(Base):
    __tablename__ = "interview_preparations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    job_application_id = Column(Integer, ForeignKey("job_applications.id", ondelete="CASCADE"))
    questions = Column(JSON)  # Array of questions
    answers = Column(JSON)    # Array of suggested answers
    created_at = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 