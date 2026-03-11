import os
import re
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

import streamlit as st


ASSET_EXTENSIONS = (".sty", ".cls", ".bst", ".ttf", ".otf", ".png", ".jpg")


def clean_latex_code(latex_code: str) -> str | None:
    """Normalize Gemini output to compilable LaTeX or return ``None``."""
    if not latex_code:
        st.error("No LaTeX code was generated.")
        return None

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


def compile_latex_to_pdf(latex_content: str, template_dir: str) -> BytesIO | None:
    """Compile LaTeX to PDF and return an in-memory PDF or ``None`` on error."""
    compiler = shutil.which("pdflatex")
    if not compiler:
        st.error("LaTeX compiler not found: 'pdflatex' is not installed or not on PATH.")
        st.info(
            "Install a TeX distribution that provides pdflatex (for example TeX Live). "
            "If you deploy on Streamlit Community Cloud, add the TeX packages to packages.txt. "
            "You can also run the app with the provided Docker image where LaTeX is preinstalled."
        )
        return None

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        tex_file_path = temp_path / "resume.tex"
        tex_file_path.write_text(latex_content, encoding="utf-8")

        if os.path.isdir(template_dir):
            for file_name in os.listdir(template_dir):
                if file_name.lower().endswith(ASSET_EXTENSIONS):
                    shutil.copy(os.path.join(template_dir, file_name), temp_dir)

        try:
            result = None
            for _ in range(2):
                result = subprocess.run(
                    [compiler, "-interaction=nonstopmode", "resume.tex"],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                )
        except FileNotFoundError:
            st.error("LaTeX compiler not found while compiling. Ensure 'pdflatex' is installed and on PATH.")
            return None
        except Exception as exc:
            st.error(f"Error during PDF compilation: {exc}")
            return None

        assert result is not None
        pdf_path = temp_path / "resume.pdf"
        if result.returncode == 0 and pdf_path.exists():
            return BytesIO(pdf_path.read_bytes())

        st.error("PDF compilation failed. Check LaTeX code for errors.")
        error_lines = [
            line
            for line in result.stdout.split("\n")
            if "Error:" in line or "Fatal error" in line
        ]
        if error_lines:
            st.text("\n".join(error_lines))
        else:
            st.text(result.stdout[-2000:] if result.stdout else "No error output captured")
        return None
