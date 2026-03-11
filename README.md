# Resume Enhancer

## Gemini API key setup

1. Create or use a `.env` file in the project root.
2. Add your Gemini key:

   ```env
   GEMINI_API_KEY=your_new_key_here
   ```

3. Restart the Streamlit app so the new environment variable is loaded.

## Important security step

A Gemini API key was previously committed in source. Rotate that key immediately in Google AI Studio / Google Cloud, then update your local `.env` with the replacement key.

## Notes

- `utils/gemini_api.py` and `main.py` now read `GEMINI_API_KEY` from the environment.
- `.env` and `api_key.txt` are ignored by Git to avoid committing secrets.
