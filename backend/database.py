from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
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
    last_name = Column(String)
    plan = Column(String, default="free")  # free, starter, premium, elite
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    stripe_customer_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    usage_records = relationship("UsageRecord", back_populates="user", cascade="all, delete-orphan")
    files = relationship("UserFile", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")

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
    
    # Relationships
    user = relationship("User", back_populates="usage_records")

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
    
    # Relationships
    user = relationship("User", back_populates="files")

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
    
    # Relationships
    user = relationship("User", back_populates="payments")

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
    
    # Relationships
    user = relationship("User")
    resume_file = relationship("UserFile")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 