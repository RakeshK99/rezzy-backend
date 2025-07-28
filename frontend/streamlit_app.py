import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import fitz  # PyMuPDF
from backend.ai_evaluator import evaluate_resume
import webbrowser
from backend.payments import create_checkout_session

if st.button("Subscribe to Rezzy+"):
    price_id = "price_1RpzUTPYNOHMmUPye2NbA1x5"
    checkout_url = create_checkout_session(price_id)
    st.markdown(f"[Click here to subscribe to Rezzy+ 🚀]({checkout_url})", unsafe_allow_html=True)
    st.stop()


st.set_page_config(page_title="Rezzy – Resume Evaluator", layout="centered")

st.title("🧠 Rezzy — AI Resume Evaluator")
st.markdown("Tailor your resume to any job description using AI.")

uploaded_file = st.file_uploader("📄 Upload your resume (PDF or TXT)", type=["pdf", "txt"])
job_description = st.text_area("💼 Paste the job description here")

def extract_text_from_file(file, file_type):
    if file_type == "pdf":
        doc = fitz.open(stream=file.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in doc])
    elif file_type == "txt":
        return file.read().decode("utf-8", errors="ignore")
    else:
        return ""

if st.button("🔍 Analyze Resume"):
    if uploaded_file and job_description:
        file_type = uploaded_file.name.split('.')[-1].lower()
        resume_text = extract_text_from_file(uploaded_file, file_type)

        with st.spinner("Analyzing with AI..."):
            result = evaluate_resume(resume_text, job_description)
        st.subheader("✅ Rezzy Results")
        st.markdown(result)
    else:
        st.warning("Please upload a resume and paste a job description.")

if not st.session_state.get("subscribed", False):
    st.warning("This feature is locked. Subscribe to Rezzy+ to access.")
    st.stop()

