import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _get_gemini_api_key() -> str | None:
    """Resolve Gemini API key from env, Streamlit secrets, or local api_key.txt."""
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key.strip()

    try:
        secret_key = st.secrets.get("GEMINI_API_KEY")
        if secret_key:
            return str(secret_key).strip()
    except Exception:
        # st.secrets may be unavailable outside a Streamlit runtime.
        pass

    key_file = Path(__file__).resolve().parent.parent / "api_key.txt"
    if key_file.exists():
        file_key = key_file.read_text(encoding="utf-8").strip()
        if file_key:
            return file_key

    return None


def call_gemini_api(prompt: str) -> str | None:
    """Call Gemini and return generated text, or ``None`` when unavailable."""
    api_key = _get_gemini_api_key()
    if not api_key:
        st.error(
            "GEMINI_API_KEY is not configured. Add it as an environment variable, "
            "Streamlit secret, or put it in api_key.txt at the project root."
        )
        return None

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={api_key}"
    )
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.8,
            "topK": 40,
            "maxOutputTokens": 8192,
        },
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
    except requests.RequestException as exc:
        st.error(f"Error calling Gemini API: {exc}")
        return None

    try:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError, ValueError):
        st.error("Unexpected response format from Gemini API.")
        return None
