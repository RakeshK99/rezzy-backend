from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
import os
import tempfile
import json
import io
from typing import Optional
import uuid
from datetime import datetime

# Import our modules
try:
    from database import get_db, User, UsageRecord, UserFile, Payment
    from user_service import UserService
    from ai_evaluator import evaluate_resume, generate_cover_letter, generate_interview_questions
    from resume_parser import parse_resume, analyze_resume_structure
    from job_parser import analyze_job_requirements, find_keyword_gaps
    from s3_service import s3_service
    from stripe_service import stripe_service as rezzy_stripe_service
    from job_matching import job_matching_service
    print("✅ All modules imported successfully")
except Exception as e:
    print(f"⚠️ Warning: Some modules failed to import: {e}")
    # Set fallback values for modules that failed to import
    get_db = None
    User = None
    UsageRecord = None
    UserFile = None
    Payment = None
    UserService = None
    evaluate_resume = None
    generate_cover_letter = None
    generate_interview_questions = None
    parse_resume = None
    analyze_resume_structure = None
    analyze_job_requirements = None
    find_keyword_gaps = None
    s3_service = None
    rezzy_stripe_service = None
    job_matching_service = None

app = FastAPI(title="Rezzy API", version="1.0.0")
router = APIRouter()

print("🚀 Rezzy API starting up...")
print(f"📦 Environment: {os.getenv('ENVIRONMENT', 'development')}")
print(f"🔧 Debug mode: {os.getenv('DEBUG', 'false')}")

# Allow CORS from frontend
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@router.get("/api/get-plan")
def get_user_plan(user_id: str, db: Session = Depends(get_db)):
    """Get user's current plan"""
    try:
        user_service = UserService(db)
        return user_service.get_user_plan(user_id)
    except Exception as e:
        print(f"Error getting user plan: {e}")
        return {
            "plan": "free",
            "usage": {"scans_used": 0, "month": datetime.utcnow().strftime("%Y-%m")},
            "limits": {"scans_per_month": 3}
        }

@router.post("/api/create-user")
async def create_user(
    user_id: str = Form(...),
    email: str = Form(...),
    first_name: str = Form(""),
    middle_name: str = Form(""),
    last_name: str = Form(""),
    db: Session = Depends(get_db)
):
    """Create a new user (called when user signs up)"""
    try:
        user_service = UserService(db)
        user = user_service.create_user(user_id, email, first_name, middle_name, last_name)
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "middle_name": user.middle_name,
                "last_name": user.last_name,
                "plan": user.plan,
                "position_level": user.position_level,
                "job_category": user.job_category
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload and parse resume file"""
    try:
        # Check file type
        if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
        # Check file size (10MB limit)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File size too large. Maximum 10MB allowed.")
        
        # Parse resume text first (before S3 upload)
        resume_text = parse_resume_from_bytes(content, file.filename)
        if not resume_text:
            raise HTTPException(
                status_code=400, 
                detail=f"Could not extract text from resume. Please ensure your {file.filename} is a valid PDF, DOCX, or DOC file and is not corrupted."
            )
        
        # Upload to S3
        import io
        file_data = io.BytesIO(content)
        file_data.seek(0)  # Reset file pointer
        s3_key = s3_service.upload_file(file_data, file.filename, user_id, "resume")
        
        if not s3_key:
            raise HTTPException(status_code=500, detail="Failed to upload file to cloud storage")
        
        # Save file record to database
        user_service = UserService(db)
        user_file = user_service.save_user_file(
            user_id, 
            f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}", 
            file.filename, 
            "resume", 
            s3_key, 
            file_size
        )
        
        # Set as current resume
        if user_file:
            user = user_service.get_user(user_id)
            if user:
                user.current_resume_id = user_file.id
                user.updated_at = datetime.utcnow()
                db.commit()
        
        # Analyze structure
        structure_analysis = analyze_resume_structure(resume_text)
        
        return {
            "success": True,
            "resume_text": resume_text,
            "structure_analysis": structure_analysis,
            "filename": file.filename,
            "file_id": user_file.id if user_file else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in upload_resume: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/api/set-current-resume")
async def set_current_resume(
    user_id: str = Form(...),
    resume_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Set a resume as the current active resume for the user"""
    try:
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify the resume belongs to the user
        resume_file = user_service.db.query(UserFile).filter(
            UserFile.id == resume_id,
            UserFile.user_id == user_id,
            UserFile.file_type == "resume"
        ).first()
        
        if not resume_file:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Set as current resume
        user.current_resume_id = resume_id
        db.commit()
        
        return {
            "success": True,
            "message": "Current resume updated successfully",
            "resume_id": resume_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error setting current resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to set current resume")

def parse_resume_from_bytes(content: bytes, filename: str) -> Optional[str]:
    """Parse resume from bytes content"""
    temp_path = None
    try:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Parse resume
        resume_text = parse_resume(temp_path)
        
        return resume_text
    except Exception as e:
        print(f"Error parsing resume from bytes: {e}")
        return None
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as cleanup_error:
                print(f"Error cleaning up temp file: {cleanup_error}")

@router.post("/api/analyze-job")
async def analyze_job(job_description: str = Form(...)):
    """Analyze job description and extract requirements"""
    try:
        analysis = analyze_job_requirements(job_description)
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/evaluate-resume")
async def evaluate_resume_endpoint(
    resume_text: str = Form(...),
    job_description: str = Form(...),
    user_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Evaluate resume against job description"""
    try:
        user_service = UserService(db)
        
        # Check usage limits for free users
        if not user_service.check_usage_limit(user_id, "scan"):
            raise HTTPException(status_code=403, detail="Monthly scan limit reached. Upgrade to continue.")
        
        # Perform AI evaluation
        ai_evaluation = evaluate_resume(resume_text, job_description)
        
        # Find keyword gaps
        keyword_gaps = find_keyword_gaps(resume_text, job_description)
        
        # Analyze job requirements
        job_analysis = analyze_job_requirements(job_description)
        
        # Save analysis results to database
        saved_analysis = user_service.save_resume_analysis(
            user_id=user_id,
            resume_text=resume_text,
            job_description=job_description,
            ai_evaluation=ai_evaluation,
            keyword_gaps=keyword_gaps,
            job_analysis=job_analysis
        )
        
        # Increment usage
        user_service.increment_usage(user_id, "scan")
        
        return {
            "success": True,
            "analysis_id": saved_analysis.id if saved_analysis else None,
            "ai_evaluation": ai_evaluation,
            "keyword_gaps": keyword_gaps,
            "job_analysis": job_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/generate-cover-letter")
async def generate_cover_letter_endpoint(
    resume_text: str = Form(...),
    job_description: str = Form(...),
    company_name: str = Form(""),
    user_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Generate cover letter (Premium feature)"""
    try:
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        
        if not user or user.plan == "free":
            raise HTTPException(status_code=403, detail="Cover letter generation is a premium feature")
        
        cover_letter = generate_cover_letter(resume_text, job_description, company_name)
        
        # Increment usage
        user_service.increment_usage(user_id, "cover_letter")
        
        return {
            "success": True,
            "cover_letter": cover_letter
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/generate-interview-questions")
async def generate_interview_questions_endpoint(
    resume_text: str = Form(...),
    job_description: str = Form(...),
    user_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Generate interview questions (Premium feature)"""
    try:
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        
        if not user or user.plan == "free":
            raise HTTPException(status_code=403, detail="Interview questions generation is a premium feature")
        
        questions = generate_interview_questions(resume_text, job_description)
        
        # Increment usage
        user_service.increment_usage(user_id, "interview_questions")
        
        return {
            "success": True,
            "questions": questions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/create-checkout-session")
async def create_checkout_session(
    user_id: str = Form(...),
    plan: str = Form(...),
    success_url: str = Form(...),
    cancel_url: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session for subscription"""
    try:
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create Stripe customer if doesn't exist
        if not user.stripe_customer_id:
            customer_id = rezzy_stripe_service.create_customer(user.email, user_id)
            if customer_id:
                user.stripe_customer_id = customer_id
                db.commit()
        
        # Create checkout session
        session_id = rezzy_stripe_service.create_checkout_session(
            user_id, plan, success_url, cancel_url
        )
        
        if not session_id:
            raise HTTPException(status_code=500, detail="Failed to create checkout session")
        
        return {
            "success": True,
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/stripe-webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        event = rezzy_stripe_service.handle_webhook(payload, sig_header)
        
        if not event:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_id = session['metadata']['user_id']
            plan = session['metadata']['plan']
            
            # Update user plan
            db = next(get_db())
            user_service = UserService(db)
            user_service.update_user_plan(user_id, plan)
            
            # Record payment
            payment = Payment(
                user_id=user_id,
                stripe_payment_intent_id=session['payment_intent'],
                amount=session['amount_total'],
                currency=session['currency'],
                plan=plan,
                status='succeeded'
            )
            db.add(payment)
            db.commit()
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/search-jobs")
async def search_jobs(
    query: str = Form(...),
    location: str = Form(""),
    limit: int = Form(10),
    user_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Search for jobs (Premium feature)"""
    try:
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        
        if not user or user.plan == "free":
            raise HTTPException(status_code=403, detail="Job search is a premium feature")
        
        jobs = job_matching_service.search_jobs_rapidapi(query, location, limit)
        
        return {
            "success": True,
            "jobs": jobs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/match-jobs")
async def match_jobs(
    user_id: str = Form(...),
    time_filter: str = Form("1w"),
    db: Session = Depends(get_db)
):
    """Get job recommendations based on user profile"""
    try:
        user_service = UserService(db)
        jobs = user_service.get_job_recommendations(user_id, time_filter)
        return {"success": True, "jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/job-recommendations/{user_id}")
async def get_job_recommendations(
    user_id: str,
    time_filter: str = "1w",
    db: Session = Depends(get_db)
):
    """Get job recommendations based on user profile"""
    try:
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's current resume if available
        current_resume_text = None
        if user.current_resume_id:
            resume_file = user_service.db.query(UserFile).filter(UserFile.id == user.current_resume_id).first()
            if resume_file:
                # Download resume content from S3
                try:
                    resume_content = s3_service.download_file(resume_file.s3_key)
                    current_resume_text = parse_resume_from_bytes(resume_content, resume_file.filename)
                except Exception as e:
                    print(f"Error downloading resume: {e}")
        
        # Get job recommendations
        recommendations = user_service.get_job_recommendations(user_id, time_filter)
        
        return {
            "user_profile": {
                "position_level": user.position_level,
                "job_category": user.job_category,
                "has_resume": bool(current_resume_text)
            },
            "recommendations": recommendations,
            "time_filter": time_filter
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting job recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job recommendations")

@router.get("/api/user-files")
async def get_user_files(
    user_id: str,
    file_type: str = None,
    db: Session = Depends(get_db)
):
    """Get user's uploaded files"""
    try:
        user_service = UserService(db)
        files = user_service.get_user_files(user_id, file_type)
        
        file_list = []
        for file in files:
            # Generate presigned URL for download
            download_url = s3_service.get_presigned_url(file.s3_key)
            
            file_list.append({
                "id": file.id,
                "filename": file.original_filename,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "created_at": file.created_at.isoformat(),
                "download_url": download_url
            })
        
        return {
            "success": True,
            "files": file_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/resume-analyses")
async def get_resume_analyses(
    user_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get user's recent resume analyses"""
    try:
        user_service = UserService(db)
        analyses = user_service.get_resume_analyses(user_id, limit)
        
        return {
            "success": True,
            "analyses": [
                {
                    "id": analysis.id,
                    "resume_text": analysis.resume_text[:200] + "..." if len(analysis.resume_text) > 200 else analysis.resume_text,
                    "job_description": analysis.job_description[:200] + "..." if len(analysis.job_description) > 200 else analysis.job_description,
                    "ai_evaluation": analysis.ai_evaluation,
                    "keyword_gaps": analysis.keyword_gaps,
                    "job_analysis": analysis.job_analysis,
                    "created_at": analysis.created_at.isoformat()
                }
                for analysis in analyses
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/resume-analysis/{analysis_id}")
async def get_resume_analysis(
    analysis_id: int,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific resume analysis"""
    try:
        user_service = UserService(db)
        analysis = user_service.get_resume_analysis(analysis_id, user_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "success": True,
            "analysis": {
                "id": analysis.id,
                "resume_text": analysis.resume_text,
                "job_description": analysis.job_description,
                "ai_evaluation": analysis.ai_evaluation,
                "keyword_gaps": analysis.keyword_gaps,
                "job_analysis": analysis.job_analysis,
                "created_at": analysis.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/health")
def health_check():
    """Health check endpoint"""
    try:
        # Basic health check without database dependency
        return {
            "status": "healthy", 
            "service": "Rezzy API", 
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/")
def root():
    """Root endpoint for Railway health check"""
    return {
        "message": "Rezzy API is running", 
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@router.post("/api/init-database")
def init_database():
    """Initialize database tables"""
    try:
        from database import Base, engine
        print("🔨 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        return {"success": True, "message": "Database tables created successfully"}
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return {"success": False, "error": str(e)}

@router.get("/api/subscription/{user_id}")
async def get_subscription(user_id: str, db: Session = Depends(get_db)):
    """Get user's subscription details"""
    try:
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        
        if not user or not user.stripe_customer_id:
            return {"subscription": None, "plan": "free"}
        
        customer = rezzy_stripe_service.get_customer(user.stripe_customer_id)
        
        if not customer:
            return {"subscription": None, "plan": "free"}
        
        # Get active subscriptions
        subscriptions = rezzy_stripe_service.get_customer_subscriptions(user.stripe_customer_id)
        active_subscription = None
        
        for sub in subscriptions:
            if sub['status'] in ['active', 'trialing']:
                active_subscription = sub
                break
        
        return {
            "subscription": active_subscription,
            "plan": user.plan,
            "customer_id": user.stripe_customer_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/cancel-subscription")
async def cancel_subscription(user_id: str = Form(...), db: Session = Depends(get_db)):
    """Cancel user's subscription"""
    try:
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        
        if not user or not user.stripe_customer_id:
            raise HTTPException(status_code=404, detail="User or subscription not found")
        
        subscriptions = rezzy_stripe_service.get_customer_subscriptions(user.stripe_customer_id)
        
        for sub in subscriptions:
            if sub['status'] in ['active', 'trialing']:
                success = rezzy_stripe_service.cancel_subscription(sub['id'])
                if success:
                    # Update user plan to free
                    user_service.update_user_plan(user_id, "free")
                    return {"success": True, "message": "Subscription cancelled successfully"}
        
        raise HTTPException(status_code=404, detail="No active subscription found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/upgrade-subscription")
async def upgrade_subscription(
    user_id: str = Form(...),
    new_plan: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upgrade user subscription"""
    try:
        print(f"🔧 Upgrade subscription called for user: {user_id}, plan: {new_plan}")
        print(f"🔧 rezzy_stripe_service is: {rezzy_stripe_service}")
        
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        print(f"🔧 User found: {user.email}")
        
        # If user has no subscription, create new one
        if not user.stripe_customer_id:
            print(f"🔧 Creating new Stripe customer for user: {user.email}")
            # Create customer first
            customer_id = rezzy_stripe_service.create_customer(user.email, user_id)
            if customer_id:
                user_service.update_stripe_customer_id(user_id, customer_id)
                print(f"🔧 Customer created: {customer_id}")
            else:
                print(f"🔧 Failed to create customer")
        
        # Create checkout session for upgrade
        success_url = f"https://end-seven.vercel.app/dashboard?success=true&plan={new_plan}"
        cancel_url = "https://end-seven.vercel.app/dashboard?canceled=true"
        
        print(f"🔧 Creating checkout session...")
        session_id = rezzy_stripe_service.create_checkout_session(
            user_id, new_plan, success_url, cancel_url
        )
        
        if session_id:
            print(f"🔧 Checkout session created: {session_id}")
            return {"success": True, "session_id": session_id}
        else:
            print(f"🔧 Failed to create checkout session")
            raise HTTPException(status_code=500, detail="Failed to create checkout session")
    except Exception as e:
        print(f"🔧 Error in upgrade_subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# New Profile Management Endpoints
@router.get("/api/profile/{user_id}")
async def get_profile(user_id: str, db: Session = Depends(get_db)):
    """Get user profile information"""
    try:
        user_service = UserService(db)
        profile = user_service.get_user_profile(user_id)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/user-profile/{user_id}")
async def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """Get complete user profile with all information"""
    try:
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get current resume if exists
        current_resume = None
        if user.current_resume_id:
            resume_file = user_service.db.query(UserFile).filter(UserFile.id == user.current_resume_id).first()
            if resume_file:
                current_resume = {
                    "id": resume_file.id,
                    "filename": resume_file.filename,
                    "original_filename": resume_file.original_filename,
                    "created_at": resume_file.created_at.isoformat()
                }
        
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "last_name": user.last_name,
            "plan": user.plan,
            "position_level": user.position_level,
            "job_category": user.job_category,
            "current_resume": current_resume,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/update-profile")
async def update_profile(
    user_id: str = Form(...),
    first_name: str = Form(...),
    middle_name: str = Form(""),
    last_name: str = Form(...),
    position_level: str = Form(""),
    job_category: str = Form(""),
    db: Session = Depends(get_db)
):
    """Update user profile information"""
    try:
        user_service = UserService(db)
        user_service.update_profile(user_id, first_name, middle_name, last_name, position_level, job_category)
        return {"success": True, "message": "Profile updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Job Application Management Endpoints
@router.get("/api/job-applications/{user_id}")
async def get_job_applications(user_id: str, db: Session = Depends(get_db)):
    """Get user's job applications"""
    try:
        user_service = UserService(db)
        applications = user_service.get_job_applications(user_id)
        return {"applications": applications}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/job-applications")
async def create_job_application(
    user_id: str = Form(...),
    job_title: str = Form(...),
    company: str = Form(...),
    location: str = Form(""),
    job_url: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    """Create a new job application"""
    try:
        user_service = UserService(db)
        application = user_service.create_job_application(user_id, job_title, company, location, job_url, notes)
        return {"success": True, "application": application}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/job-applications/{application_id}")
async def update_job_application(
    application_id: int,
    user_id: str = Form(...),
    job_title: str = Form(...),
    company: str = Form(...),
    location: str = Form(""),
    job_url: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    """Update a job application"""
    try:
        user_service = UserService(db)
        application = user_service.update_job_application(application_id, user_id, job_title, company, location, job_url, notes)
        return {"success": True, "application": application}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/job-applications/{application_id}/status")
async def update_application_status(
    application_id: int,
    user_id: str = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    """Update job application status"""
    try:
        user_service = UserService(db)
        application = user_service.update_application_status(application_id, user_id, status)
        return {"success": True, "application": application}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/job-applications/{application_id}")
async def delete_job_application(
    application_id: int,
    user_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Delete a job application"""
    try:
        user_service = UserService(db)
        user_service.delete_job_application(application_id, user_id)
        return {"success": True, "message": "Application deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Optimized Resume Endpoints
@router.get("/api/optimized-resumes/{user_id}")
async def get_optimized_resumes(user_id: str, db: Session = Depends(get_db)):
    """Get user's optimized resumes"""
    try:
        user_service = UserService(db)
        resumes = user_service.get_optimized_resumes(user_id)
        return {"resumes": resumes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/optimize-resume")
async def optimize_resume(
    user_id: str = Form(...),
    job_title: str = Form(...),
    company: str = Form(...),
    job_description: str = Form(...),
    job_requirements: str = Form(...),
    db: Session = Depends(get_db)
):
    """Optimize resume for a specific job"""
    try:
        user_service = UserService(db)
        optimized_resume = user_service.optimize_resume(user_id, job_title, company, job_description, job_requirements)
        return {"success": True, "optimized_resume": optimized_resume}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/generate-optimized-resume")
async def generate_optimized_resume(
    user_id: str = Form(...),
    job_title: str = Form(...),
    company: str = Form(...),
    job_description: str = Form(...),
    job_requirements: str = Form(...),
    db: Session = Depends(get_db)
):
    """Generate an optimized resume for a specific job posting"""
    try:
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's current resume
        if not user.current_resume_id:
            raise HTTPException(status_code=400, detail="No resume uploaded. Please upload a resume first.")
        
        resume_file = user_service.db.query(UserFile).filter(UserFile.id == user.current_resume_id).first()
        if not resume_file:
            raise HTTPException(status_code=404, detail="Current resume not found")
        
        # Download resume content from S3
        try:
            resume_content = s3_service.download_file(resume_file.s3_key)
            original_resume_text = parse_resume_from_bytes(resume_content, resume_file.filename)
        except Exception as e:
            print(f"Error downloading resume: {e}")
            raise HTTPException(status_code=500, detail="Failed to download resume")
        
        if not original_resume_text:
            raise HTTPException(status_code=400, detail="Could not parse resume content")
        
        # Generate optimized resume using AI
        try:
            from ai_evaluator import optimize_resume_for_job
            optimized_content = optimize_resume_for_job(original_resume_text, job_description, job_requirements)
        except Exception as e:
            print(f"Error optimizing resume: {e}")
            raise HTTPException(status_code=500, detail="Failed to optimize resume")
        
        # Save optimized resume
        optimized_filename = f"optimized_{job_title.replace(' ', '_')}_{company.replace(' ', '_')}.pdf"
        s3_key = f"optimized_resumes/{user_id}/{optimized_filename}"
        
        # Convert optimized content to PDF (you'll need to implement this)
        # For now, we'll save as text
        optimized_content_bytes = optimized_content.encode('utf-8')
        s3_service.upload_file(optimized_content_bytes, s3_key)
        
        # Save to database
        optimized_file = user_service.save_user_file(
            user_id=user_id,
            filename=optimized_filename,
            original_filename=optimized_filename,
            file_type="optimized_resume",
            s3_key=s3_key,
            file_size=len(optimized_content_bytes)
        )
        
        return {
            "success": True,
            "optimized_resume_id": optimized_file.id,
            "filename": optimized_filename,
            "message": "Optimized resume generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating optimized resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate optimized resume")

@router.get("/api/download-optimized-resume/{resume_id}")
async def download_optimized_resume(resume_id: int, user_id: str, db: Session = Depends(get_db)):
    """Download optimized resume as PDF"""
    try:
        user_service = UserService(db)
        pdf_content = user_service.generate_optimized_resume_pdf(resume_id, user_id)
        return FileResponse(
            io.BytesIO(pdf_content),
            media_type='application/pdf',
            filename=f'optimized_resume_{resume_id}.pdf'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Interview Preparation Endpoints
@router.get("/api/interview-preparations/{user_id}")
async def get_interview_preparations(user_id: str, db: Session = Depends(get_db)):
    """Get user's interview preparations"""
    try:
        user_service = UserService(db)
        preparations = user_service.get_interview_preparations(user_id)
        return {"preparations": preparations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/generate-interview-prep")
async def generate_interview_prep(
    user_id: str = Form(...),
    job_application_id: str = Form(...),
    job_title: str = Form(...),
    company: str = Form(...),
    job_description: str = Form(""),
    db: Session = Depends(get_db)
):
    """Generate interview preparation for a job application"""
    try:
        user_service = UserService(db)
        preparation = user_service.generate_interview_preparation(user_id, job_application_id, job_title, company, job_description)
        return {"success": True, "preparation": preparation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Download Resume Endpoint
@router.get("/api/download-resume/{file_id}")
async def download_resume(file_id: int, user_id: str, db: Session = Depends(get_db)):
    """Download user's resume file"""
    try:
        user_service = UserService(db)
        file_content, filename = user_service.download_resume(file_id, user_id)
        return FileResponse(
            io.BytesIO(file_content),
            media_type='application/octet-stream',
            filename=filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
