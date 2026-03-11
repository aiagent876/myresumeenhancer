import base64
import os

import streamlit as st

from utils.file_handling import extract_resume_content
from utils.gemini_api import call_gemini_api
from utils.latex_processing import clean_latex_code, compile_latex_to_pdf

TEMPLATE_DIR = os.path.join(os.getcwd(), "templates")


# Load templates
def load_template(template_name: str) -> str | None:
    template_path = os.path.join(TEMPLATE_DIR, f"{template_name}.tex")
    try:
        with open(template_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        st.error(f"Template '{template_name}' not found at {template_path}.")
        return None


st.title("Resume Enhancer with Gemini AI")
st.write("Upload your resume and paste the job description to generate an enhanced resume.")

template_choice = st.selectbox("Choose a LaTeX template", ["Classic", "Modern"])
uploaded_file = st.file_uploader("Upload your resume (PDF or text)", type=["pdf", "txt"])

if uploaded_file:
    resume_text = extract_resume_content(uploaded_file)

    st.write("Resume uploaded successfully!")

    # Display a preview of the extracted text
    with st.expander("Preview extracted resume text"):
        st.text(resume_text[:1000] + ("..." if len(resume_text) > 1000 else ""))

    # Job description input
    jd = st.text_area("Paste the job description here:")

    # Additional options
    with st.expander("Advanced Options"):
        company_name = st.text_input("Company Name (Optional, will be extracted from JD if not provided)")
        position_name = st.text_input("Position Title (Optional, will be extracted from JD if not provided)")

    if st.button("Enhance Resume"):
        if not jd.strip():
            st.warning("Please paste the job description.")
        else:
            selected_template = load_template(template_choice)
            if not selected_template:
                st.stop()

            prompt = f"""
            You are a professional resume writer with expertise in LaTeX. Your task is to enhance a resume for a job application by tailoring it to match the specific job description.

            ## TEMPLATE:
            ```latex
            {selected_template}
            ```

            ## RESUME CONTENT:
            ```
            {resume_text}
            ```

            ## JOB DESCRIPTION:
            ```
            {jd}
            ```

            ## COMPANY AND POSITION DETAILS:
            Company: {company_name if company_name else "Extract from job description"}
            Position: {position_name if position_name else "Extract from job description"}

            ## INSTRUCTIONS:
            1. Create a complete LaTeX resume document using the provided template.
            2. Tailor the content to highlight skills and experiences that match the job description.
            3. Keep the original LaTeX structure and commands intact.
            4. Ensure all LaTeX special characters are properly escaped.
            5. Focus on skills and experiences most relevant to the job description.
            6. Ensure the document compiles correctly without errors.
            7. Return ONLY the complete LaTeX code with no explanations or markdown.

            The LaTeX code should start with the document class and end with \\end{{document}}.
            """

            with st.spinner("Enhancing your resume... This may take a minute."):
                enhanced_resume = call_gemini_api(prompt)

            if not enhanced_resume:
                st.error("Failed to enhance resume. Please try again.")
                st.stop()

            clean_resume = clean_latex_code(enhanced_resume)
            if clean_resume is None:
                st.warning("Using raw model output because cleaned LaTeX could not be validated.")
                clean_resume = enhanced_resume

            st.success("Resume enhanced successfully!")

            with st.expander("View LaTeX Code"):
                st.code(clean_resume, language="latex")

            with st.spinner("Compiling PDF..."):
                pdf_data = compile_latex_to_pdf(clean_resume, TEMPLATE_DIR)

            if pdf_data:
                st.success("PDF compiled successfully!")
                st.download_button(
                    label="📥 Download Enhanced Resume (PDF)",
                    data=pdf_data,
                    file_name="enhanced_resume.pdf",
                    mime="application/pdf",
                )

                st.write("PDF Preview:")
                st.write("(If the preview doesn't appear, you can still download the PDF using the button above)")

                base64_pdf = base64.b64encode(pdf_data.getvalue()).decode("utf-8")
                pdf_display = (
                    f'<iframe src="data:application/pdf;base64,{base64_pdf}" '
                    'width="700" height="1000" type="application/pdf"></iframe>'
                )
                st.markdown(pdf_display, unsafe_allow_html=True)
            else:
                st.error("Failed to compile PDF. Please check for LaTeX errors.")
