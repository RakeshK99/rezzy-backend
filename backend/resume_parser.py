import PyMuPDF
import docx2txt
import os
from typing import Optional

def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """Extract text from PDF file using PyMuPDF"""
    try:
        doc = PyMuPDF.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def extract_text_from_docx(file_path: str) -> Optional[str]:
    """Extract text from DOCX file using docx2txt"""
    try:
        text = docx2txt.process(file_path)
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return None

def parse_resume(file_path: str) -> Optional[str]:
    """Parse resume file and extract text content"""
    if not os.path.exists(file_path):
        return None
    
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")

def analyze_resume_structure(resume_text: str) -> dict:
    """Analyze resume structure for ATS compatibility"""
    analysis = {
        "word_count": len(resume_text.split()),
        "has_contact_info": any(keyword in resume_text.lower() for keyword in ["email", "phone", "@"]),
        "has_education": any(keyword in resume_text.lower() for keyword in ["education", "degree", "university", "college"]),
        "has_experience": any(keyword in resume_text.lower() for keyword in ["experience", "work", "employment", "job"]),
        "has_skills": any(keyword in resume_text.lower() for keyword in ["skills", "technologies", "programming", "languages"]),
        "recommendations": []
    }
    
    # Generate recommendations
    if analysis["word_count"] < 200:
        analysis["recommendations"].append("Resume seems too short. Consider adding more details about your experience.")
    elif analysis["word_count"] > 800:
        analysis["recommendations"].append("Resume might be too long. Consider condensing to 1-2 pages.")
    
    if not analysis["has_contact_info"]:
        analysis["recommendations"].append("Add contact information (email, phone).")
    
    if not analysis["has_education"]:
        analysis["recommendations"].append("Include education section.")
    
    if not analysis["has_experience"]:
        analysis["recommendations"].append("Add work experience section.")
    
    if not analysis["has_skills"]:
        analysis["recommendations"].append("Include skills section.")
    
    return analysis
