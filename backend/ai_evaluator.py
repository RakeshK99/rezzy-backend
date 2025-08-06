import openai
import os
import json
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def evaluate_resume(resume_text: str, job_description: str) -> Dict:
    """Evaluate resume against job description using AI"""
    
    prompt = f"""
    You are an expert resume evaluator and career coach. Analyze the following resume against the job description and provide a detailed evaluation.

    Job Description:
    {job_description}

    Resume:
    {resume_text}

    Please provide your analysis in the following JSON format:
    {{
        "match_score": 85,
        "overall_assessment": "Strong match with room for improvement",
        "strengths": [
            "Good technical skills alignment",
            "Relevant experience in the field"
        ],
        "weaknesses": [
            "Missing some key technologies",
            "Could improve quantifiable achievements"
        ],
        "missing_keywords": [
            "python",
            "aws",
            "leadership"
        ],
        "suggested_improvements": [
            "Add specific metrics to achievements",
            "Include more relevant keywords",
            "Highlight leadership experience"
        ],
        "improved_bullet_points": [
            "Led a team of 5 developers to deliver a web application that increased user engagement by 40%",
            "Implemented AWS cloud infrastructure reducing costs by 25%",
            "Developed Python-based automation tools saving 15 hours per week"
        ],
        "ats_compatibility_score": 90,
        "ats_recommendations": [
            "Use standard section headers",
            "Include relevant keywords naturally",
            "Avoid graphics and tables"
        ]
    }}

    Focus on providing actionable, specific feedback that will help the candidate improve their resume for this specific job.
    """

    try:
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        
        response_text = chat_completion.choices[0].message.content
        
        # Try to parse JSON response
        try:
            # Extract JSON from response (in case there's extra text)
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            
            result = json.loads(json_str)
            return result
        except json.JSONDecodeError:
            # Fallback to parsing the text response
            return parse_text_response(response_text)
            
    except Exception as e:
        print(f"Error in AI evaluation: {e}")
        return {
            "match_score": 50,
            "overall_assessment": "Unable to complete analysis",
            "strengths": [],
            "weaknesses": ["Technical error occurred"],
            "missing_keywords": [],
            "suggested_improvements": ["Please try again"],
            "improved_bullet_points": [],
            "ats_compatibility_score": 50,
            "ats_recommendations": []
        }

def parse_text_response(response_text: str) -> Dict:
    """Parse text response when JSON parsing fails"""
    # Simple parsing logic for fallback
    lines = response_text.split('\n')
    
    result = {
        "match_score": 70,
        "overall_assessment": "Analysis completed",
        "strengths": [],
        "weaknesses": [],
        "missing_keywords": [],
        "suggested_improvements": [],
        "improved_bullet_points": [],
        "ats_compatibility_score": 80,
        "ats_recommendations": []
    }
    
    # Extract match score if present
    for line in lines:
        if "match score" in line.lower() or "score" in line.lower():
            try:
                score = int(''.join(filter(str.isdigit, line)))
                if 0 <= score <= 100:
                    result["match_score"] = score
            except:
                pass
    
    return result

def generate_cover_letter(resume_text: str, job_description: str, company_name: str = "the company") -> str:
    """Generate a cover letter using AI"""
    
    prompt = f"""
    Write a professional cover letter for the following job application.

    Job Description:
    {job_description}

    Resume Summary:
    {resume_text[:500]}...

    Company: {company_name}

    Write a compelling cover letter that:
    1. Addresses the hiring manager professionally
    2. Shows enthusiasm for the role
    3. Highlights relevant experience from the resume
    4. Explains why you're a good fit for the company
    5. Ends with a call to action

    Keep it concise (200-300 words) and professional.
    """

    try:
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error generating cover letter: {e}"

def generate_interview_questions(resume_text: str, job_description: str) -> List[str]:
    """Generate interview questions based on resume and job description"""
    
    prompt = f"""
    Generate 5-7 relevant interview questions for a candidate with this resume applying for this job.

    Job Description:
    {job_description}

    Resume:
    {resume_text}

    Generate questions that:
    1. Probe into specific experiences mentioned in the resume
    2. Test knowledge of technologies/skills required for the job
    3. Assess problem-solving and communication abilities
    4. Are relevant to the specific role and industry

    Return only the questions, one per line, without numbering.
    """

    try:
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        
        questions = chat_completion.choices[0].message.content.strip().split('\n')
        return [q.strip() for q in questions if q.strip()]
    except Exception as e:
        return [f"Error generating questions: {e}"]

def optimize_resume_for_job(resume_text: str, job_description: str, job_requirements: str = "") -> str:
    """Optimize resume content for a specific job without adding false information"""
    
    prompt = f"""
    You are an expert resume writer. Optimize the following resume for the specific job description and requirements.
    
    IMPORTANT: Do NOT add any false information, made-up experiences, or skills that are not already present in the original resume. 
    Only reorganize, rephrase, and emphasize existing content to better match the job requirements.
    
    Job Description:
    {job_description}
    
    Job Requirements:
    {job_requirements}
    
    Original Resume:
    {resume_text}
    
    Please optimize the resume by:
    1. Reorganizing sections to highlight relevant experience first
    2. Rephrasing bullet points to include relevant keywords from the job description
    3. Emphasizing achievements and experiences that match the job requirements
    4. Improving the overall structure and flow
    5. Making sure all content is factual and based on the original resume
    
    Return the optimized resume content in a clean, professional format.
    Do not add any explanations or notes - just return the optimized resume text.
    """

    try:
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error optimizing resume: {e}")
        return resume_text  # Return original if optimization fails

if __name__ == "__main__":
    resume_text = "Experienced Python developer with strong data analysis skills. Proficient in SQL and cloud tools."
    job_description = "We are looking for someone with experience in Python, AWS, machine learning, and communication skills."

    try:
        result = evaluate_resume(resume_text, job_description)
        print("\n=== Rezzy AI Output ===\n")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("❌ Error occurred:", e)

