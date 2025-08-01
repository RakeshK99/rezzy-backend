import requests
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

load_dotenv()

class JobMatchingService:
    def __init__(self):
        self.linkedin_api_key = os.getenv('LINKEDIN_API_KEY')
        self.indeed_api_key = os.getenv('INDEED_API_KEY')
        self.rapid_api_key = os.getenv('RAPID_API_KEY')
    
    def search_jobs_linkedin(self, keywords: str, location: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Search jobs using LinkedIn API (requires LinkedIn API access)"""
        try:
            # This is a placeholder - you'll need LinkedIn API credentials
            # LinkedIn API requires special approval and setup
            headers = {
                'Authorization': f'Bearer {self.linkedin_api_key}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'keywords': keywords,
                'location': location,
                'limit': limit
            }
            
            # Placeholder response - replace with actual LinkedIn API call
            return []
            
        except Exception as e:
            print(f"Error searching LinkedIn jobs: {e}")
            return []
    
    def search_jobs_indeed(self, query: str, location: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Search jobs using Indeed API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.indeed_api_key}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'query': query,
                'location': location,
                'limit': limit
            }
            
            # Placeholder response - replace with actual Indeed API call
            return []
            
        except Exception as e:
            print(f"Error searching Indeed jobs: {e}")
            return []
    
    def search_jobs_rapidapi(self, query: str, location: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Search jobs using RapidAPI (multiple job sources)"""
        try:
            headers = {
                'X-RapidAPI-Key': self.rapid_api_key,
                'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
            }
            
            params = {
                'query': query,
                'location': location,
                'num_pages': '1',
                'page': '1'
            }
            
            response = requests.get(
                'https://jsearch.p.rapidapi.com/search',
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = []
                
                for job in data.get('data', [])[:limit]:
                    jobs.append({
                        'title': job.get('job_title', ''),
                        'company': job.get('employer_name', ''),
                        'location': job.get('job_city', ''),
                        'description': job.get('job_description', ''),
                        'requirements': job.get('job_required_skills', ''),
                        'salary': job.get('job_salary', ''),
                        'job_type': job.get('job_employment_type', ''),
                        'source': 'rapidapi',
                        'source_url': job.get('job_apply_link', ''),
                        'posted_date': job.get('job_posted_at_datetime_utc', ''),
                        'experience_level': self._extract_experience_level(job.get('job_description', ''))
                    })
                
                return jobs
            else:
                print(f"RapidAPI error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error searching jobs via RapidAPI: {e}")
            return []
    
    def match_resume_to_jobs(self, resume_text: str, job_description: str, location: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Match resume to relevant job postings"""
        try:
            # Extract key skills and keywords from resume
            from job_parser import extract_keywords_from_job_description
            
            # Use job description as search query (since it contains the role we're looking for)
            search_query = self._extract_search_query(job_description)
            
            # Search for jobs
            jobs = self.search_jobs_rapidapi(search_query, location, limit * 2)
            
            # Score and rank jobs based on resume match
            scored_jobs = []
            for job in jobs:
                score = self._calculate_job_match_score(resume_text, job['description'])
                job['match_score'] = score
                scored_jobs.append(job)
            
            # Sort by match score and return top results
            scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
            return scored_jobs[:limit]
            
        except Exception as e:
            print(f"Error matching resume to jobs: {e}")
            return []
    
    def _extract_search_query(self, job_description: str) -> str:
        """Extract search query from job description"""
        # Simple extraction - look for job title patterns
        lines = job_description.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip().lower()
            if any(keyword in line for keyword in ['developer', 'engineer', 'manager', 'analyst', 'specialist']):
                return line
        
        # Fallback to first line
        return lines[0].strip() if lines else "software developer"
    
    def _calculate_job_match_score(self, resume_text: str, job_description: str) -> float:
        """Calculate match score between resume and job description"""
        try:
            from job_parser import find_keyword_gaps
            
            # Get keyword gaps (missing keywords)
            gaps = find_keyword_gaps(resume_text, job_description)
            
            # Calculate score based on coverage percentage
            coverage = gaps.get('coverage_percentage', 0)
            
            # Normalize to 0-100 scale
            score = min(100, max(0, coverage))
            
            return score
            
        except Exception as e:
            print(f"Error calculating job match score: {e}")
            return 50.0  # Default score
    
    def _extract_experience_level(self, description: str) -> str:
        """Extract experience level from job description"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['senior', 'lead', 'principal', 'architect']):
            return 'senior'
        elif any(word in description_lower for word in ['mid', 'intermediate', '3+ years', '4+ years']):
            return 'mid'
        elif any(word in description_lower for word in ['junior', 'entry', 'graduate', '0-2 years']):
            return 'entry'
        else:
            return 'mid'  # Default
    
    def get_job_details(self, job_id: str, source: str) -> Optional[Dict[str, Any]]:
        """Get detailed job information"""
        try:
            if source == 'rapidapi':
                headers = {
                    'X-RapidAPI-Key': self.rapid_api_key,
                    'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
                }
                
                response = requests.get(
                    f'https://jsearch.p.rapidapi.com/job-details',
                    headers=headers,
                    params={'job_id': job_id}
                )
                
                if response.status_code == 200:
                    return response.json()
            
            return None
            
        except Exception as e:
            print(f"Error getting job details: {e}")
            return None

# Global job matching service instance
job_matching_service = JobMatchingService() 