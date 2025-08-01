import re
from typing import List, Dict, Set

def extract_keywords_from_job_description(job_description: str) -> Dict[str, List[str]]:
    """Extract key information from job description"""
    
    # Common technical skills
    technical_skills = [
        "python", "javascript", "java", "c++", "c#", "php", "ruby", "go", "rust", "swift", "kotlin",
        "react", "angular", "vue", "node.js", "express", "django", "flask", "spring", "laravel",
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "git", "github",
        "machine learning", "ai", "data science", "pandas", "numpy", "tensorflow", "pytorch",
        "html", "css", "bootstrap", "tailwind", "sass", "less",
        "agile", "scrum", "kanban", "jira", "confluence"
    ]
    
    # Soft skills
    soft_skills = [
        "leadership", "communication", "teamwork", "problem solving", "analytical thinking",
        "creativity", "adaptability", "time management", "organization", "attention to detail",
        "customer service", "project management", "collaboration", "mentoring", "presentation"
    ]
    
    # Experience levels
    experience_levels = [
        "entry level", "junior", "mid level", "senior", "lead", "principal", "architect",
        "intern", "graduate", "experienced", "expert"
    ]
    
    # Education requirements
    education = [
        "bachelor", "master", "phd", "degree", "diploma", "certification", "certified"
    ]
    
    job_lower = job_description.lower()
    
    # Extract found keywords
    found_technical = [skill for skill in technical_skills if skill in job_lower]
    found_soft = [skill for skill in soft_skills if skill in job_lower]
    found_experience = [level for level in experience_levels if level in job_lower]
    found_education = [edu for edu in education if edu in job_lower]
    
    # Extract years of experience
    years_pattern = r'(\d+)[\+]?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)'
    years_match = re.findall(years_pattern, job_lower)
    years_required = [int(year) for year in years_match] if years_match else []
    
    # Extract salary information
    salary_pattern = r'\$(\d{1,3}(?:,\d{3})*(?:-\d{1,3}(?:,\d{3})*)?)\s*(?:k|k\+|per\s*year|annually)'
    salary_matches = re.findall(salary_pattern, job_lower)
    
    return {
        "technical_skills": found_technical,
        "soft_skills": found_soft,
        "experience_level": found_experience,
        "education_requirements": found_education,
        "years_required": years_required,
        "salary_info": salary_matches
    }

def analyze_job_requirements(job_description: str) -> Dict:
    """Analyze job requirements and provide insights"""
    keywords = extract_keywords_from_job_description(job_description)
    
    analysis = {
        "keywords": keywords,
        "total_requirements": len(keywords["technical_skills"]) + len(keywords["soft_skills"]),
        "difficulty_level": "entry",
        "recommendations": []
    }
    
    # Determine difficulty level
    if keywords["years_required"]:
        max_years = max(keywords["years_required"])
        if max_years <= 2:
            analysis["difficulty_level"] = "entry"
        elif max_years <= 5:
            analysis["difficulty_level"] = "mid"
        else:
            analysis["difficulty_level"] = "senior"
    
    # Generate recommendations
    if len(keywords["technical_skills"]) > 10:
        analysis["recommendations"].append("This role requires many technical skills. Focus on the most relevant ones for your resume.")
    
    if keywords["years_required"] and max(keywords["years_required"]) > 5:
        analysis["recommendations"].append("This is a senior-level position. Emphasize leadership and project experience.")
    
    return analysis

def find_keyword_gaps(resume_text: str, job_description: str) -> Dict:
    """Find missing keywords from job description in resume"""
    resume_lower = resume_text.lower()
    job_keywords = extract_keywords_from_job_description(job_description)
    
    missing_technical = [skill for skill in job_keywords["technical_skills"] if skill not in resume_lower]
    missing_soft = [skill for skill in job_keywords["soft_skills"] if skill not in resume_lower]
    
    return {
        "missing_technical_skills": missing_technical,
        "missing_soft_skills": missing_soft,
        "total_missing": len(missing_technical) + len(missing_soft),
        "coverage_percentage": round(((len(job_keywords["technical_skills"]) + len(job_keywords["soft_skills"]) - len(missing_technical) - len(missing_soft)) / max(1, len(job_keywords["technical_skills"]) + len(job_keywords["soft_skills"]))) * 100, 1)
    }
