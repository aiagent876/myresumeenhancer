import streamlit as st
import requests
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import PyPDF2
from io import BytesIO
from dotenv import load_dotenv


# Access the API key from Streamlit secrets
api_key = st.secrets["GEMINI_API_KEY"]

# Load environment variables from .env file
load_dotenv()

# Fetch the API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Debug: Print the API key to verify it's loaded correctly
print("Debug: Loaded API Key:", GEMINI_API_KEY)

# Set the template directory path relative to the current working directory
TEMPLATE_DIR = os.path.join(os.getcwd(), "templates")

# Debug: Print the template directory path
print("Debug: Template Directory:", TEMPLATE_DIR)

# Function to call Gemini API
def call_gemini_api(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.8,
            "topK": 40,
            "maxOutputTokens": 8192
        }
    }

    # Debug: Print the API URL and payload
    print("Debug: API URL:", url)
    print("Debug: API Payload:", data)

    try:
        response = requests.post(url, json=data, headers=headers)
        # Debug: Print the API response status code and content
        print("Debug: API Response Status Code:", response.status_code)
        print("Debug: API Response Content:", response.json())

        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            st.error(f"Error calling Gemini API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error during API call: {e}")
        return None

# Function to compile LaTeX to PDF in an isolated environment
def compile_latex_to_pdf(latex_content):
    # Create a temporary directory for compilation
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write LaTeX content to a file
        tex_file_path = Path(temp_dir) / "resume.tex"
        with open(tex_file_path, "w", encoding="utf-8") as f:
            f.write(latex_content)
        
        # Debug: Print the LaTeX content being compiled
        print("Debug: LaTeX Content:", latex_content)

        # Copy any required assets from template directory to temp directory
        for file in os.listdir(TEMPLATE_DIR):
            if file.endswith(('.sty', '.cls', '.bst', '.ttf', '.otf', '.png', '.jpg')):
                shutil.copy(os.path.join(TEMPLATE_DIR, file), temp_dir)
        
        # Compile LaTeX to PDF
        try:
            # Change to the temporary directory
            original_dir = os.getcwd()
            os.chdir(temp_dir)
            
            # Run pdflatex twice to resolve references
            for _ in range(2):
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "resume.tex"],
                    capture_output=True, text=True
                )
            
            # Debug: Print the pdflatex output
            print("Debug: pdflatex Output:", result.stdout)
            print("Debug: pdflatex Errors:", result.stderr)

            # Check if PDF was generated
            pdf_path = Path(temp_dir) / "resume.pdf"
            if result.returncode == 0 and pdf_path.exists():
                with open(pdf_path, "rb") as pdf_file:
                    pdf_data = BytesIO(pdf_file.read())
                
                # Return to original directory
                os.chdir(original_dir)
                return pdf_data
            else:
                # Return to original directory
                os.chdir(original_dir)
                
                st.error("PDF compilation failed. Check LaTeX code for errors.")
                # Show meaningful error message from pdflatex output
                error_output = result.stdout
                error_lines = [line for line in error_output.split('\n') if "Error:" in line or "Fatal error" in line]
                if error_lines:
                    st.text("\n".join(error_lines))
                else:
                    st.text(error_output[-2000:] if error_output else "No error output captured")
                return None
        except Exception as e:
            # Make sure we return to the original directory
            os.chdir(original_dir)
            st.error(f"Error during PDF compilation: {e}")
            return None

# Load templates
def load_template(template_name):
    template_path = os.path.join(TEMPLATE_DIR, f"{template_name}.tex")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"Template '{template_name}' not found at {template_path}.")
        return None

# Extract text from PDF file
def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return ""

# Clean and format LaTeX code from API response
def clean_latex_code(latex_code):
    # Remove markdown code blocks if present
    if "```latex" in latex_code or "```" in latex_code:
        import re
        match = re.search(r"```(?:latex)?\s*([\s\S]*?)```", latex_code)
        if match:
            latex_code = match.group(1).strip()
        else:
            latex_code = latex_code.replace("```latex", "").replace("```", "").strip()
    
    # Ensure proper document structure
    if not "\\begin{document}" in latex_code:
        st.warning("Generated LaTeX is missing document structure. Using template as base.")
        return None
    
    return latex_code

# Streamlit UI
st.title("Resume Enhancer with Gemini AI")
st.write("Upload your resume and paste the job description to generate an enhanced resume.")

# Template selection
template_choice = st.selectbox("Choose a LaTeX template", ["Classic", "Modern"])

# Resume upload
uploaded_file = st.file_uploader("Upload your resume (PDF or text)", type=["pdf", "txt"])

if uploaded_file:
    # Extract resume text
    if uploaded_file.type == "application/pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    else:
        resume_text = uploaded_file.read().decode("utf-8")
    
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
            # Load the selected template
            selected_template = load_template(template_choice)
            if not selected_template:
                st.stop()
            
            # Create a more structured prompt for the API
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

            # Debug: Print the prompt being sent to the API
            print("Debug: Prompt Sent to API:", prompt)

            with st.spinner("Enhancing your resume... This may take a minute."):
                enhanced_resume = call_gemini_api(prompt)
                if enhanced_resume:
                    # Clean up the LaTeX code
                    clean_resume = clean_latex_code(enhanced_resume)
                    
                    if clean_resume is None:
                        # Use the original template as a base and try to insert the content
                        st.warning("Using the original template as a base. Some customization may be lost.")
                        clean_resume = enhanced_resume
                    
                    st.success("Resume enhanced successfully!")
                    
                    # Display LaTeX code
                    with st.expander("View LaTeX Code"):
                        st.code(clean_resume, language="latex")
                    
                    # Compile the LaTeX code to PDF
                    with st.spinner("Compiling PDF..."):
                        pdf_data = compile_latex_to_pdf(clean_resume)
                        
                    if pdf_data:
                        st.success("PDF compiled successfully!")
                        st.download_button(
                            label="📥 Download Enhanced Resume (PDF)",
                            data=pdf_data,
                            file_name="enhanced_resume.pdf",
                            mime="application/pdf"
                        )
                        
                        # Display a preview of the PDF
                        st.write("PDF Preview:")
                        st.write("(If the preview doesn't appear, you can still download the PDF using the button above)")
                        
                        # Create a base64 encoded PDF for display
                        import base64
                        base64_pdf = base64.b64encode(pdf_data.getvalue()).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                    else:
                        st.error("Failed to compile PDF. Please check for LaTeX errors.")
                else:
                    st.error("Failed to enhance resume. Please try again.")
