import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def call_gemini_api(prompt: str) -> str | None:
    """Call Gemini and return generated text, or ``None`` when unavailable."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("GEMINI_API_KEY is not configured.")
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
