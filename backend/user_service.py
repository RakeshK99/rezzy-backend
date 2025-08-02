from sqlalchemy.orm import Session
from database import User, UsageRecord, UserFile, Payment, ResumeAnalysis
from datetime import datetime
from typing import Optional, Dict, Any
import os

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_id: str, email: str, first_name: str = "", last_name: str = "") -> User:
        """Create a new user with free plan"""
        try:
            # Check if user already exists by ID
            existing_user = self.db.query(User).filter(User.id == user_id).first()
            if existing_user:
                return existing_user
            
            # Check if email already exists (for users who might have signed up before)
            existing_email_user = self.db.query(User).filter(User.email == email).first()
            if existing_email_user:
                # Update the existing user's ID to match the new user_id
                existing_email_user.id = user_id
                existing_email_user.first_name = first_name
                existing_email_user.last_name = last_name
                existing_email_user.updated_at = datetime.utcnow()
                self.db.commit()
                return existing_email_user
            
            # Create new user
            user = User(
                id=user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                plan="free",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(user)
            
            # Create initial usage record
            current_month = datetime.utcnow().strftime("%Y-%m")
            usage_record = UsageRecord(
                user_id=user_id,
                month=current_month,
                scans_used=0,
                cover_letters_generated=0,
                interview_questions_generated=0
            )
            
            self.db.add(usage_record)
            self.db.commit()
            
            return user
            
        except Exception as e:
            self.db.rollback()
            print(f"Error creating user: {e}")
            raise
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            return self.db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_user_plan(self, user_id: str) -> Dict[str, Any]:
        """Get user's current plan and usage"""
        try:
            user = self.get_user(user_id)
            if not user:
                # Create user if doesn't exist (for new signups)
                return self._get_default_plan_response()
            
            # Get current month usage
            current_month = datetime.utcnow().strftime("%Y-%m")
            usage_record = self.db.query(UsageRecord).filter(
                UsageRecord.user_id == user_id,
                UsageRecord.month == current_month
            ).first()
            
            if not usage_record:
                # Create usage record for current month
                usage_record = UsageRecord(
                    user_id=user_id,
                    month=current_month,
                    scans_used=0,
                    cover_letters_generated=0,
                    interview_questions_generated=0
                )
                self.db.add(usage_record)
                self.db.commit()
            
            return {
                "plan": user.plan,
                "usage": {
                    "scans_used": usage_record.scans_used,
                    "month": current_month
                },
                "limits": self._get_plan_limits(user.plan)
            }
            
        except Exception as e:
            print(f"Error getting user plan: {e}")
            return self._get_default_plan_response()
    
    def update_user_plan(self, user_id: str, new_plan: str) -> bool:
        """Update user's plan"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            user.plan = new_plan
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error updating user plan: {e}")
            return False
    
    def increment_usage(self, user_id: str, usage_type: str) -> bool:
        """Increment usage for a specific type"""
        try:
            current_month = datetime.utcnow().strftime("%Y-%m")
            usage_record = self.db.query(UsageRecord).filter(
                UsageRecord.user_id == user_id,
                UsageRecord.month == current_month
            ).first()
            
            if not usage_record:
                usage_record = UsageRecord(
                    user_id=user_id,
                    month=current_month,
                    scans_used=0,
                    cover_letters_generated=0,
                    interview_questions_generated=0
                )
                self.db.add(usage_record)
            
            if usage_type == "scan":
                usage_record.scans_used += 1
            elif usage_type == "cover_letter":
                usage_record.cover_letters_generated += 1
            elif usage_type == "interview_questions":
                usage_record.interview_questions_generated += 1
            
            usage_record.updated_at = datetime.utcnow()
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error incrementing usage: {e}")
            return False
    
    def check_usage_limit(self, user_id: str, usage_type: str) -> bool:
        """Check if user has exceeded usage limits"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            plan_limits = self._get_plan_limits(user.plan)
            
            if usage_type == "scan":
                current_month = datetime.utcnow().strftime("%Y-%m")
                usage_record = self.db.query(UsageRecord).filter(
                    UsageRecord.user_id == user_id,
                    UsageRecord.month == current_month
                ).first()
                
                if not usage_record:
                    return True  # No usage yet, so within limits
                
                scan_limit = plan_limits.get("scans_per_month", 3)
                if scan_limit == -1:  # Unlimited
                    return True
                
                return usage_record.scans_used < scan_limit
            
            return True  # Other usage types don't have limits for now
            
        except Exception as e:
            print(f"Error checking usage limit: {e}")
            return False
    
    def save_user_file(self, user_id: str, filename: str, original_filename: str, 
                      file_type: str, s3_key: str, file_size: int) -> Optional[UserFile]:
        """Save user file record"""
        try:
            user_file = UserFile(
                user_id=user_id,
                filename=filename,
                original_filename=original_filename,
                file_type=file_type,
                s3_key=s3_key,
                file_size=file_size,
                created_at=datetime.utcnow()
            )
            
            self.db.add(user_file)
            self.db.commit()
            return user_file
            
        except Exception as e:
            self.db.rollback()
            print(f"Error saving user file: {e}")
            return None
    
    def get_user_files(self, user_id: str, file_type: str = None) -> list:
        """Get user's files"""
        try:
            query = self.db.query(UserFile).filter(UserFile.user_id == user_id)
            if file_type:
                query = query.filter(UserFile.file_type == file_type)
            
            return query.order_by(UserFile.created_at.desc()).all()
            
        except Exception as e:
            print(f"Error getting user files: {e}")
            return []

    def save_resume_analysis(self, user_id: str, resume_text: str, job_description: str, 
                           ai_evaluation: dict, keyword_gaps: dict, job_analysis: dict, 
                           resume_file_id: int = None) -> Optional[ResumeAnalysis]:
        """Save resume analysis results"""
        try:
            import json
            
            analysis = ResumeAnalysis(
                user_id=user_id,
                resume_file_id=resume_file_id,
                resume_text=resume_text,
                job_description=job_description,
                ai_evaluation=json.dumps(ai_evaluation),
                keyword_gaps=json.dumps(keyword_gaps),
                job_analysis=json.dumps(job_analysis),
                created_at=datetime.utcnow()
            )
            
            self.db.add(analysis)
            self.db.commit()
            return analysis
            
        except Exception as e:
            self.db.rollback()
            print(f"Error saving resume analysis: {e}")
            return None

    def get_resume_analyses(self, user_id: str, limit: int = 10) -> list:
        """Get user's recent resume analyses"""
        try:
            import json
            
            analyses = self.db.query(ResumeAnalysis).filter(
                ResumeAnalysis.user_id == user_id
            ).order_by(ResumeAnalysis.created_at.desc()).limit(limit).all()
            
            # Convert JSON strings back to dictionaries
            for analysis in analyses:
                try:
                    analysis.ai_evaluation = json.loads(analysis.ai_evaluation) if analysis.ai_evaluation else {}
                    analysis.keyword_gaps = json.loads(analysis.keyword_gaps) if analysis.keyword_gaps else {}
                    analysis.job_analysis = json.loads(analysis.job_analysis) if analysis.job_analysis else {}
                except json.JSONDecodeError:
                    analysis.ai_evaluation = {}
                    analysis.keyword_gaps = {}
                    analysis.job_analysis = {}
            
            return analyses
            
        except Exception as e:
            print(f"Error getting resume analyses: {e}")
            return []

    def get_resume_analysis(self, analysis_id: int, user_id: str) -> Optional[ResumeAnalysis]:
        """Get a specific resume analysis"""
        try:
            import json
            
            analysis = self.db.query(ResumeAnalysis).filter(
                ResumeAnalysis.id == analysis_id,
                ResumeAnalysis.user_id == user_id
            ).first()
            
            if analysis:
                # Convert JSON strings back to dictionaries
                try:
                    analysis.ai_evaluation = json.loads(analysis.ai_evaluation) if analysis.ai_evaluation else {}
                    analysis.keyword_gaps = json.loads(analysis.keyword_gaps) if analysis.keyword_gaps else {}
                    analysis.job_analysis = json.loads(analysis.job_analysis) if analysis.job_analysis else {}
                except json.JSONDecodeError:
                    analysis.ai_evaluation = {}
                    analysis.keyword_gaps = {}
                    analysis.job_analysis = {}
            
            return analysis
            
        except Exception as e:
            print(f"Error getting resume analysis: {e}")
            return None
    
    def _get_plan_limits(self, plan: str) -> Dict[str, Any]:
        """Get limits for a specific plan"""
        limits = {
            "free": {
                "scans_per_month": 3,
                "cover_letters_per_month": 0,
                "interview_questions_per_month": 0
            },
            "starter": {
                "scans_per_month": -1,  # Unlimited
                "cover_letters_per_month": 0,
                "interview_questions_per_month": 0
            },
            "premium": {
                "scans_per_month": -1,  # Unlimited
                "cover_letters_per_month": -1,  # Unlimited
                "interview_questions_per_month": -1  # Unlimited
            },
            "elite": {
                "scans_per_month": -1,  # Unlimited
                "cover_letters_per_month": -1,  # Unlimited
                "interview_questions_per_month": -1  # Unlimited
            }
        }
        
        return limits.get(plan, limits["free"])
    
    def _get_default_plan_response(self) -> Dict[str, Any]:
        """Get default plan response for new users"""
        return {
            "plan": "free",
            "usage": {
                "scans_used": 0,
                "month": datetime.utcnow().strftime("%Y-%m")
            },
            "limits": self._get_plan_limits("free")
        } 