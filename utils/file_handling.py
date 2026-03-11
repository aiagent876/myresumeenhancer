import PyPDF2
import streamlit as st


def extract_resume_content(uploaded_file) -> str:
    """Extract text from uploaded PDF/TXT file and return a string."""
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += (page.extract_text() or "") + "\n"
            return text

        return uploaded_file.read().decode("utf-8")
    except Exception as exc:
        st.error(f"Error extracting resume text: {exc}")
        return ""
