from sqlalchemy.orm import Session
from database import User, UsageRecord, UserFile, Payment
from datetime import datetime
from typing import Optional, Dict, Any
import os

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_id: str, email: str, first_name: str = "", last_name: str = "") -> User:
        """Create a new user with free plan"""
        try:
            # Check if user already exists
            existing_user = self.db.query(User).filter(User.id == user_id).first()
            if existing_user:
                return existing_user
            
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