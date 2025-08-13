from sqlalchemy.orm import Session
from database import User, UsageRecord, UserFile, Payment, ResumeAnalysis, JobApplication, OptimizedResume, InterviewPreparation
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import os
import json

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_id: str, email: str, first_name: str = "", middle_name: str = "", last_name: str = "") -> User:
        """Create a new user with free plan"""
        try:
            # Check if user already exists by ID
            existing_user = self.db.query(User).filter(User.id == user_id).first()
            if existing_user:
                # Update existing user with new information
                existing_user.first_name = first_name
                existing_user.middle_name = middle_name
                existing_user.last_name = last_name
                existing_user.updated_at = datetime.utcnow()
                self.db.commit()
                return existing_user
            
            # Check if email already exists (for users who might have signed up before)
            existing_email_user = self.db.query(User).filter(User.email == email).first()
            if existing_email_user:
                # If the existing user has a different ID, we need to handle this carefully
                if existing_email_user.id != user_id:
                    # Delete existing usage records for the old user ID
                    self.db.query(UsageRecord).filter(UsageRecord.user_id == existing_email_user.id).delete()
                    
                    # Update the existing user's ID to match the new user_id
                    existing_email_user.id = user_id
                    existing_email_user.first_name = first_name
                    existing_email_user.middle_name = middle_name
                    existing_email_user.last_name = last_name
                    existing_email_user.updated_at = datetime.utcnow()
                    self.db.commit()
                    
                    # Create new usage record for the new user ID
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
                    return existing_email_user
                else:
                    # Same user ID, just update the info
                    existing_email_user.first_name = first_name
                    existing_email_user.middle_name = middle_name
                    existing_email_user.last_name = last_name
                    existing_email_user.updated_at = datetime.utcnow()
                    self.db.commit()
                    return existing_email_user
            
            # Create new user first
            user = User(
                id=user_id,
                email=email,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                plan="free",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add user to session and commit
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # Now create usage record after user is committed
            try:
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
            except Exception as usage_error:
                # If usage record creation fails, log it but don't fail the user creation
                print(f"Warning: Could not create usage record for user {user_id}: {usage_error}")
                # Don't rollback the user creation
            
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
                "scans_per_month": 5,
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
    
    def update_stripe_customer_id(self, user_id: str, stripe_customer_id: str) -> bool:
        """Update user's Stripe customer ID"""
        try:
            user = self.get_user(user_id)
            if user:
                user.stripe_customer_id = stripe_customer_id
                user.updated_at = datetime.utcnow()
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            print(f"Error updating stripe customer ID: {e}")
            return False

    # Profile Management Methods
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile information"""
        try:
            user = self.get_user(user_id)
            if not user:
                return {}
            
            current_resume = None
            if user.current_resume_id:
                resume_file = self.db.query(UserFile).filter(UserFile.id == user.current_resume_id).first()
                if resume_file:
                    current_resume = {
                        "id": resume_file.id,
                        "filename": resume_file.filename,
                        "original_filename": resume_file.original_filename
                    }
            
            return {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "middle_name": user.middle_name,
                "last_name": user.last_name,
                "position_level": user.position_level,
                "job_category": user.job_category,
                "current_resume": current_resume
            }
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return {}

    def update_profile(self, user_id: str, first_name: str, middle_name: str, last_name: str, 
                      position_level: str, job_category: str) -> bool:
        """Update user profile information"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            user.first_name = first_name
            user.middle_name = middle_name
            user.last_name = last_name
            user.position_level = position_level
            user.job_category = job_category
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error updating profile: {e}")
            return False

    # Job Application Methods
    def get_job_applications(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's job applications"""
        try:
            applications = self.db.query(JobApplication).filter(
                JobApplication.user_id == user_id
            ).order_by(JobApplication.application_date.desc()).all()
            
            return [
                {
                    "id": app.id,
                    "job_title": app.job_title,
                    "company": app.company,
                    "location": app.location,
                    "job_url": app.job_url,
                    "application_status": app.application_status,
                    "application_date": app.application_date.isoformat(),
                    "last_updated": app.last_updated.isoformat(),
                    "notes": app.notes,
                    "match_score": app.match_score,
                    "job_description": app.job_description
                }
                for app in applications
            ]
        except Exception as e:
            print(f"Error getting job applications: {e}")
            return []

    def create_job_application(self, user_id: str, job_title: str, company: str, 
                             location: str, job_url: str, notes: str) -> Dict[str, Any]:
        """Create a new job application"""
        try:
            application = JobApplication(
                user_id=user_id,
                job_title=job_title,
                company=company,
                location=location,
                job_url=job_url,
                notes=notes,
                application_status="applied",
                application_date=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            
            self.db.add(application)
            self.db.commit()
            self.db.refresh(application)
            
            return {
                "id": application.id,
                "job_title": application.job_title,
                "company": application.company,
                "location": application.location,
                "job_url": application.job_url,
                "application_status": application.application_status,
                "application_date": application.application_date.isoformat(),
                "last_updated": application.last_updated.isoformat(),
                "notes": application.notes
            }
        except Exception as e:
            self.db.rollback()
            print(f"Error creating job application: {e}")
            raise

    def update_job_application(self, application_id: int, user_id: str, job_title: str, 
                             company: str, location: str, job_url: str, notes: str) -> Dict[str, Any]:
        """Update a job application"""
        try:
            application = self.db.query(JobApplication).filter(
                JobApplication.id == application_id,
                JobApplication.user_id == user_id
            ).first()
            
            if not application:
                raise ValueError("Application not found")
            
            application.job_title = job_title
            application.company = company
            application.location = location
            application.job_url = job_url
            application.notes = notes
            application.last_updated = datetime.utcnow()
            
            self.db.commit()
            
            return {
                "id": application.id,
                "job_title": application.job_title,
                "company": application.company,
                "location": application.location,
                "job_url": application.job_url,
                "application_status": application.application_status,
                "application_date": application.application_date.isoformat(),
                "last_updated": application.last_updated.isoformat(),
                "notes": application.notes
            }
        except Exception as e:
            self.db.rollback()
            print(f"Error updating job application: {e}")
            raise

    def update_application_status(self, application_id: int, user_id: str, status: str) -> Dict[str, Any]:
        """Update job application status"""
        try:
            application = self.db.query(JobApplication).filter(
                JobApplication.id == application_id,
                JobApplication.user_id == user_id
            ).first()
            
            if not application:
                raise ValueError("Application not found")
            
            application.application_status = status
            application.last_updated = datetime.utcnow()
            
            self.db.commit()
            
            return {
                "id": application.id,
                "job_title": application.job_title,
                "company": application.company,
                "application_status": application.application_status,
                "last_updated": application.last_updated.isoformat()
            }
        except Exception as e:
            self.db.rollback()
            print(f"Error updating application status: {e}")
            raise

    def delete_job_application(self, application_id: int, user_id: str) -> bool:
        """Delete a job application"""
        try:
            application = self.db.query(JobApplication).filter(
                JobApplication.id == application_id,
                JobApplication.user_id == user_id
            ).first()
            
            if not application:
                return False
            
            self.db.delete(application)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting job application: {e}")
            return False

    # Optimized Resume Methods
    def get_optimized_resumes(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's optimized resumes"""
        try:
            resumes = self.db.query(OptimizedResume).filter(
                OptimizedResume.user_id == user_id
            ).order_by(OptimizedResume.created_at.desc()).all()
            
            return [
                {
                    "id": resume.id,
                    "job_title": resume.job_title,
                    "company": resume.company,
                    "optimized_content": resume.optimized_content,
                    "optimization_notes": resume.optimization_notes,
                    "match_score": resume.match_score,
                    "created_at": resume.created_at.isoformat()
                }
                for resume in resumes
            ]
        except Exception as e:
            print(f"Error getting optimized resumes: {e}")
            return []

    def optimize_resume(self, user_id: str, job_title: str, company: str, 
                       job_description: str, job_requirements: str) -> Dict[str, Any]:
        """Optimize resume for a specific job"""
        try:
            # Get user's current resume
            user = self.get_user(user_id)
            if not user or not user.current_resume_id:
                raise ValueError("No resume uploaded")
            
            resume_file = self.db.query(UserFile).filter(UserFile.id == user.current_resume_id).first()
            if not resume_file:
                raise ValueError("Resume file not found")
            
            # For now, we'll create a simple optimization
            # In a real implementation, this would use AI to optimize the resume
            optimized_content = f"Optimized resume for {job_title} at {company}\n\n"
            optimized_content += f"Job Description: {job_description[:200]}...\n\n"
            optimized_content += f"Requirements: {job_requirements[:200]}...\n\n"
            optimized_content += "Optimized content would be generated here using AI..."
            
            optimized_resume = OptimizedResume(
                user_id=user_id,
                original_resume_id=user.current_resume_id,
                job_title=job_title,
                company=company,
                optimized_content=optimized_content,
                optimization_notes="Resume optimized for specific job requirements",
                match_score=85.0,  # Mock score
                created_at=datetime.utcnow()
            )
            
            self.db.add(optimized_resume)
            self.db.commit()
            self.db.refresh(optimized_resume)
            
            return {
                "id": optimized_resume.id,
                "job_title": optimized_resume.job_title,
                "company": optimized_resume.company,
                "optimized_content": optimized_resume.optimized_content,
                "optimization_notes": optimized_resume.optimization_notes,
                "match_score": optimized_resume.match_score,
                "created_at": optimized_resume.created_at.isoformat()
            }
        except Exception as e:
            self.db.rollback()
            print(f"Error optimizing resume: {e}")
            raise

    def generate_optimized_resume_pdf(self, resume_id: int, user_id: str) -> bytes:
        """Generate PDF for optimized resume"""
        try:
            resume = self.db.query(OptimizedResume).filter(
                OptimizedResume.id == resume_id,
                OptimizedResume.user_id == user_id
            ).first()
            
            if not resume:
                raise ValueError("Resume not found")
            
            # For now, return a simple text-based PDF
            # In a real implementation, this would generate a proper PDF
            content = f"Optimized Resume\n\n"
            content += f"Job: {resume.job_title}\n"
            content += f"Company: {resume.company}\n\n"
            content += resume.optimized_content
            
            return content.encode('utf-8')
        except Exception as e:
            print(f"Error generating PDF: {e}")
            raise

    # Interview Preparation Methods
    def get_interview_preparations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's interview preparations"""
        try:
            preparations = self.db.query(InterviewPreparation).filter(
                InterviewPreparation.user_id == user_id
            ).order_by(InterviewPreparation.created_at.desc()).all()
            
            return [
                {
                    "id": prep.id,
                    "job_application_id": prep.job_application_id,
                    "questions": prep.questions,
                    "answers": prep.answers,
                    "created_at": prep.created_at.isoformat()
                }
                for prep in preparations
            ]
        except Exception as e:
            print(f"Error getting interview preparations: {e}")
            return []

    def generate_interview_preparation(self, user_id: str, job_application_id: str, 
                                     job_title: str, company: str, job_description: str) -> Dict[str, Any]:
        """Generate interview preparation for a job application"""
        try:
            # For now, we'll create mock questions and answers
            # In a real implementation, this would use AI to generate relevant questions
            questions = [
                f"Tell me about your experience with {job_title}",
                f"Why are you interested in working at {company}?",
                "What are your greatest strengths and weaknesses?",
                "Where do you see yourself in 5 years?",
                "Why should we hire you for this position?"
            ]
            
            answers = [
                "I have extensive experience in this field...",
                f"I'm excited about {company}'s mission and culture...",
                "My greatest strength is my ability to...",
                "In 5 years, I hope to...",
                "I believe I'm the best candidate because..."
            ]
            
            preparation = InterviewPreparation(
                user_id=user_id,
                job_application_id=int(job_application_id),
                questions=questions,
                answers=answers,
                created_at=datetime.utcnow()
            )
            
            self.db.add(preparation)
            self.db.commit()
            self.db.refresh(preparation)
            
            return {
                "id": preparation.id,
                "job_application_id": preparation.job_application_id,
                "questions": preparation.questions,
                "answers": preparation.answers,
                "created_at": preparation.created_at.isoformat()
            }
        except Exception as e:
            self.db.rollback()
            print(f"Error generating interview preparation: {e}")
            raise

    # Job Recommendations Method
    def get_job_recommendations(self, user_id: str, time_filter: str = "1w") -> List[Dict[str, Any]]:
        """Get job recommendations based on user profile"""
        try:
            user = self.get_user(user_id)
            if not user:
                return []
            
            # Try to get real job data first
            try:
                from job_matching import job_matching_service
                if job_matching_service:
                    # Build search query based on user profile
                    search_query = self._build_search_query(user)
                    
                    # Get real job data
                    real_jobs = job_matching_service.search_jobs_rapidapi(
                        query=search_query,
                        location="",  # Could be made configurable
                        limit=10
                    )
                    
                    if real_jobs:
                        # Add match scores and format for frontend
                        for job in real_jobs:
                            job['match_score'] = self._calculate_match_score(user, job)
                            job['id'] = hash(f"{job['title']}{job['company']}") % 1000000  # Simple ID generation
                        
                        return real_jobs
            except Exception as e:
                print(f"Error getting real job data: {e}")
                # Fall back to mock data
            
            # Calculate date range based on time filter
            now = datetime.utcnow()
            if time_filter == "24h":
                start_date = now - timedelta(days=1)
            elif time_filter == "3d":
                start_date = now - timedelta(days=3)
            elif time_filter == "1w":
                start_date = now - timedelta(weeks=1)
            elif time_filter == "1m":
                start_date = now - timedelta(days=30)
            else:
                start_date = datetime(2020, 1, 1)  # All time
            
            # Fallback to mock job recommendations
            mock_jobs = [
                {
                    "id": 1,
                    "title": f"Senior {user.job_category or 'Software'} Engineer",
                    "company": "Tech Corp",
                    "location": "San Francisco, CA",
                    "description": "We're looking for a talented engineer...",
                    "requirements": "5+ years experience, Python, React...",
                    "salary_range": "$120k - $180k",
                    "job_type": "full-time",
                    "experience_level": "senior",
                    "source": "LinkedIn",
                    "source_url": "https://linkedin.com/jobs/123",
                    "created_at": (now - timedelta(days=2)).isoformat(),
                    "match_score": 92
                },
                {
                    "id": 2,
                    "title": f"{user.job_category or 'Software'} Engineer",
                    "company": "Startup Inc",
                    "location": "Remote",
                    "description": "Join our fast-growing startup...",
                    "requirements": "3+ years experience, JavaScript, Node.js...",
                    "salary_range": "$90k - $130k",
                    "job_type": "full-time",
                    "experience_level": "mid",
                    "source": "Indeed",
                    "source_url": "https://indeed.com/jobs/456",
                    "created_at": (now - timedelta(days=5)).isoformat(),
                    "match_score": 87
                }
            ]
            
            return mock_jobs
        except Exception as e:
            print(f"Error getting job recommendations: {e}")
            return []
    
    def _build_search_query(self, user) -> str:
        """Build search query based on user profile"""
        query_parts = []
        
        if user.job_category:
            query_parts.append(user.job_category)
        
        if user.position_level:
            query_parts.append(user.position_level)
        
        # Add common tech keywords
        if user.job_category and "software" in user.job_category.lower():
            query_parts.extend(["developer", "engineer", "programming"])
        elif user.job_category and "data" in user.job_category.lower():
            query_parts.extend(["data", "analytics", "machine learning"])
        elif user.job_category and "ml" in user.job_category.lower():
            query_parts.extend(["machine learning", "AI", "artificial intelligence"])
        
        return " ".join(query_parts) if query_parts else "software engineer"
    
    def _calculate_match_score(self, user, job: Dict[str, Any]) -> int:
        """Calculate match score between user profile and job"""
        score = 50  # Base score
        
        # Match job category
        if user.job_category and user.job_category.lower() in job.get('title', '').lower():
            score += 20
        
        # Match position level
        if user.position_level:
            user_level = user.position_level.lower()
            job_title = job.get('title', '').lower()
            
            if user_level in job_title:
                score += 15
            elif user_level == "intern" and "intern" in job_title:
                score += 15
            elif user_level == "senior" and "senior" in job_title:
                score += 15
            elif user_level == "staff" and "staff" in job_title:
                score += 15
        
        # Bonus for remote jobs
        if "remote" in job.get('location', '').lower():
            score += 5
        
        return min(score, 100)  # Cap at 100

    # Download Resume Method
    def download_resume(self, file_id: int, user_id: str) -> tuple:
        """Download user's resume file"""
        try:
            file = self.db.query(UserFile).filter(
                UserFile.id == file_id,
                UserFile.user_id == user_id,
                UserFile.file_type == "resume"
            ).first()
            
            if not file:
                raise ValueError("File not found")
            
            # In a real implementation, this would download from S3
            # For now, return mock content
            content = f"Resume content for {file.original_filename}"
            return content.encode('utf-8'), file.original_filename
        except Exception as e:
            print(f"Error downloading resume: {e}")
            raise 