from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
import os
import tempfile
import json
from typing import Optional
import uuid
from datetime import datetime

# Import our modules
from database import get_db, User, UsageRecord, UserFile, Payment
from user_service import UserService
from ai_evaluator import evaluate_resume, generate_cover_letter, generate_interview_questions
from resume_parser import parse_resume, analyze_resume_structure
from job_parser import analyze_job_requirements, find_keyword_gaps
from s3_service import s3_service
from stripe_service import stripe_service
from job_matching import job_matching_service

app = FastAPI(title="Rezzy API", version="1.0.0")
router = APIRouter()

# Allow CORS from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-domain.com"],  # Add your production domain
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
    last_name: str = Form(""),
    db: Session = Depends(get_db)
):
    """Create a new user (called when user signs up)"""
    try:
        user_service = UserService(db)
        user = user_service.create_user(user_id, email, first_name, last_name)
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "plan": user.plan
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
            customer_id = stripe_service.create_customer(user.email, user_id)
            if customer_id:
                user.stripe_customer_id = customer_id
                db.commit()
        
        # Create checkout session
        session_id = stripe_service.create_checkout_session(
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
        
        event = stripe_service.handle_webhook(payload, sig_header)
        
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
    resume_text: str = Form(...),
    job_description: str = Form(...),
    location: str = Form(""),
    limit: int = Form(10),
    user_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Match resume to relevant jobs (Premium feature)"""
    try:
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        
        if not user or user.plan == "free":
            raise HTTPException(status_code=403, detail="Job matching is a premium feature")
        
        matched_jobs = job_matching_service.match_resume_to_jobs(
            resume_text, job_description, location, limit
        )
        
        return {
            "success": True,
            "jobs": matched_jobs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    return {"status": "healthy", "service": "Rezzy API", "timestamp": datetime.utcnow().isoformat()}

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
