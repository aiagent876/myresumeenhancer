# Resume Enhancer

Resume Enhancer is a Streamlit app that tailors a resume to a target job description using Google Gemini, then compiles the generated LaTeX into a downloadable PDF.

## Project purpose

The project automates a resume-customization workflow:

- Ingest a candidate resume (PDF or TXT).
- Accept a target job description.
- Ask Gemini to rewrite resume content so it better aligns with the role.
- Return complete LaTeX.
- Compile that LaTeX into a PDF the user can review and download.

## Architecture

The app is currently implemented as a single Streamlit entrypoint (`main.py`) with helper modules and template files:

- **UI + orchestration:** `main.py`
  - Handles file upload, template selection, job description input, and output rendering.
- **LLM integration:** Gemini REST call in `call_gemini_api(...)`.
- **Document handling:**
  - Resume text extraction from uploaded PDFs via `PyPDF2`.
  - LaTeX cleanup/validation via `clean_latex_code(...)`.
  - PDF compilation via local `pdflatex` in a temporary directory.
- **Templates:** `templates/Classic.tex` and `templates/Modern.tex`.

## Request flow

End-to-end flow (resume upload → Gemini prompt → LaTeX → PDF):

1. User uploads a resume (`.pdf` or `.txt`) and pastes a job description in Streamlit.
2. App extracts resume text:
   - PDF: parse with `PyPDF2`.
   - TXT: decode plain text.
3. App loads the selected LaTeX template from `templates/`.
4. App builds a structured prompt containing:
   - The full selected template,
   - Extracted resume text,
   - Job description,
   - Optional company and position hints,
   - Rules to output only compilable LaTeX.
5. App sends the prompt to Gemini (`gemini-2.0-flash`) using `GEMINI_API_KEY`.
6. App receives generated LaTeX and strips markdown fences if present.
7. App writes `resume.tex` in a temporary build directory and runs `pdflatex` twice.
8. On success, app exposes the generated `resume.pdf` for preview + download.

## Local setup

### 1) Prerequisites

- **Python:** 3.9+ (Docker image is based on Python 3.9).
- **System dependency:** a LaTeX distribution including `pdflatex` and common packages (see troubleshooting if compilation fails).

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure Gemini API key

The app now resolves `GEMINI_API_KEY` in this order:

1. Environment variable `GEMINI_API_KEY` (recommended).
2. Streamlit secret `GEMINI_API_KEY`.
3. `api_key.txt` in the project root (single-line key).

Option A — `.env` file in project root:

```env
GEMINI_API_KEY=your_api_key_here
```

Option B — Streamlit secrets (`.streamlit/secrets.toml`):

```toml
GEMINI_API_KEY = "your_api_key_here"
```

Option C — project file:

```text
api_key.txt
# contains only: your_api_key_here
```

### 4) Run Streamlit

```bash
streamlit run main.py
```

By default, Streamlit serves on `http://localhost:8501`.

## Docker usage

### Build image

```bash
docker build -t resume-enhancer .
```

### Run container

```bash
docker run --rm -p 8501:8501 --env GEMINI_API_KEY=your_api_key_here resume-enhancer
```

- App URL: `http://localhost:8501`
- Exposed container port: `8501`

## Troubleshooting

### 1) Missing TeX packages / `pdflatex` errors

Symptoms:

- `pdflatex: command not found`
- LaTeX package/class errors like `! LaTeX Error: File 'xyz.sty' not found.`

Fixes:

- Install a fuller TeX distribution (e.g., TeX Live packages used in the Dockerfile).
- If using Docker, rebuild image to ensure TeX packages were installed.
- Add missing packages referenced by your selected template.

### 2) Gemini API errors

Symptoms:

- HTTP 4xx/5xx from Gemini call.
- Empty/failed enhancement response.

Fixes:

- Verify `GEMINI_API_KEY` is set and valid.
- Confirm the key has access to Gemini API and quota is available.
- Retry after checking transient API/network status.

### 3) PDF compile failures

Symptoms:

- Streamlit shows “PDF compilation failed”.
- LaTeX compiles with fatal errors.

Fixes:

- Inspect generated LaTeX in the “View LaTeX Code” expander.
- Check for unescaped special characters (`_`, `%`, `&`, etc.) in model output.
- Retry generation with slightly revised job description input.
- Temporarily simplify template complexity to isolate problematic sections.

## Security notes

- **Never commit API keys or secrets** to version control.
- Use a local `.env` file (or secret manager in production) for credentials.
- Rotate credentials immediately if a key is exposed in logs, commits, screenshots, or chat.
- Prefer least-privilege keys and monitor usage/anomalies regularly.
