import openai
import os
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def evaluate_resume(resume_text, job_description):
    prompt = f"""
    You are a resume evaluator. Analyze the following resume based on the job description.

    Job Description:
    {job_description}

    Resume:
    {resume_text}

    Give the following in response:
    1. Match score (%) from 0–100.
    2. List of missing important keywords.
    3. 2–3 improved bullet points tailored to the job description.
    """

    chat_completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    return chat_completion.choices[0].message.content

if __name__ == "__main__":
    resume_text = "Experienced Python developer with strong data analysis skills. Proficient in SQL and cloud tools."
    job_description = "We are looking for someone with experience in Python, AWS, machine learning, and communication skills."

    try:
        result = evaluate_resume(resume_text, job_description)
        print("\n=== Rezzy AI Output ===\n")
        print(result)
    except Exception as e:
        print("❌ Error occurred:", e)

