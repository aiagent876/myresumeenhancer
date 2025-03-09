import PyPDF2

def extract_resume_content(uploaded_file):
    """
    Extracts text content from an uploaded file (PDF or TXT).
    """
    if uploaded_file.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        return "".join([page.extract_text() for page in pdf_reader.pages])
    else:
        return uploaded_file.read().decode("utf-8")
