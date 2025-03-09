import re
import subprocess
import os
from io import BytesIO
import streamlit as st

def clean_latex_response(response_text):
    """
    Cleans and escapes special characters in the LaTeX response.
    """
    response_text = response_text.strip("`")  # Remove code block markers
    response_text = re.sub(r'^latex\n', '', response_text, flags=re.IGNORECASE)  # Remove leading "latex" tag
    response_text = re.sub(r'(?<!\\)&', r'\\&', response_text)  # Escape &
    response_text = re.sub(r'(?<!\\)%', r'\\%', response_text)  # Escape %
    response_text = re.sub(r'(?<!\\)\$', r'\\$', response_text)  # Escape $
    response_text = re.sub(r'(?<!\\)_', r'\\_', response_text)  # Escape _
    response_text = re.sub(r'\\newline', r'', response_text)  # Remove extraneous newlines
    return response_text

def compile_latex_to_pdf(latex_content):
    """
    Compiles LaTeX content to a PDF and returns it as an in-memory file.
    """
    tex_file = "resume.tex"

    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(latex_content)

    try:
        # Run pdflatex to generate the PDF
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_file],
            capture_output=True, text=True
        )

        if result.returncode == 0 and os.path.exists("resume.pdf"):
            with open("resume.pdf", "rb") as pdf_file:
                return BytesIO(pdf_file.read())  # Return PDF as in-memory file
        else:
            st.error("PDF compilation failed. Check LaTeX code for errors.")
            st.text("LaTeX Compilation Output:")
            st.text(result.stdout[-2000:] if result.stdout else "No output captured")
            return None
    except Exception as e:
        st.error(f"Error during PDF compilation: {e}")
        return None
    finally:
        # Clean up temporary files
        if os.path.exists(tex_file):
            os.remove(tex_file)
        if os.path.exists("resume.pdf"):
            os.remove("resume.pdf")
