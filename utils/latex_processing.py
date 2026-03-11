import os
import re
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

import streamlit as st

MAX_LATEX_SIZE_BYTES = 250_000
MAX_OUTPUT_PDF_BYTES = 5_000_000
COMPILE_TIMEOUT_SECONDS = 20
MAX_COMPILE_RUNS = 2

DISALLOWED_LATEX_PATTERNS = [
    (r"\\write18\\b", "\\write18 is not allowed."),
    (r"\\immediate\\s*\\write18\\b", "Immediate shell write is not allowed."),
    (r"\\openout\\b", "Writing files from LaTeX is not allowed."),
    (r"\\(?:input|include)\\s*\\|", "Piped input/include commands are not allowed."),
    (r"\\(?:input|include)\\s*\{\s*(?:/|[A-Za-z]:|\\\\)", "Absolute external paths are not allowed."),
    (r"\\(?:input|include)\\s*\{\s*\.\.", "Parent-directory includes are not allowed."),
]


def clean_latex_code(latex_code: str) -> str | None:
    """Extract LaTeX from markdown fences and ensure document structure is present."""
    if "```latex" in latex_code or "```" in latex_code:
        match = re.search(r"```(?:latex)?\s*([\s\S]*?)```", latex_code)
        if match:
            latex_code = match.group(1).strip()
        else:
            latex_code = latex_code.replace("```latex", "").replace("```", "").strip()

    if "\\begin{document}" not in latex_code:
        st.warning("Generated LaTeX is missing document structure.")
        return None

    return latex_code


def clean_latex_response(response_text: str) -> str:
    """Backward-compatible alias for older callers."""
    return clean_latex_code(response_text) or response_text


def validate_latex_for_compilation(latex_content: str) -> str | None:
    latex_size = len(latex_content.encode("utf-8"))
    if latex_size > MAX_LATEX_SIZE_BYTES:
        return "Input LaTeX is too large."

    for pattern, message in DISALLOWED_LATEX_PATTERNS:
        if re.search(pattern, latex_content, flags=re.IGNORECASE):
            return message

    return None


def compile_latex_to_pdf(latex_content: str, template_dir: str) -> BytesIO | None:
    """Compile LaTeX in an isolated temp directory with strict flags and limits."""
    validation_error = validate_latex_for_compilation(latex_content)
    if validation_error:
        st.error(f"Blocked unsafe LaTeX content: {validation_error}")
        return None

    with tempfile.TemporaryDirectory() as temp_dir:
        tex_file_path = Path(temp_dir) / "resume.tex"
        tex_file_path.write_text(latex_content, encoding="utf-8")

        for file_name in os.listdir(template_dir):
            if file_name.endswith((".sty", ".cls", ".bst", ".ttf", ".otf", ".png", ".jpg", ".jpeg")):
                shutil.copy(os.path.join(template_dir, file_name), temp_dir)

        try:
            result = None
            for _ in range(MAX_COMPILE_RUNS):
                result = subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        "-halt-on-error",
                        "-no-shell-escape",
                        "resume.tex",
                    ],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=COMPILE_TIMEOUT_SECONDS,
                )

            assert result is not None
            pdf_path = Path(temp_dir) / "resume.pdf"
            if result.returncode != 0 or not pdf_path.exists():
                st.error("PDF compilation failed. Check LaTeX code for errors.")
                output = result.stdout or result.stderr or "No output captured"
                st.text(output[-2000:])
                return None

            if pdf_path.stat().st_size > MAX_OUTPUT_PDF_BYTES:
                st.error("Generated PDF is too large and was blocked.")
                return None

            return BytesIO(pdf_path.read_bytes())
        except subprocess.TimeoutExpired:
            st.error("PDF compilation timed out due to resource limits.")
            return None
        except Exception as exc:
            st.error(f"Error during PDF compilation: {exc}")
            return None
