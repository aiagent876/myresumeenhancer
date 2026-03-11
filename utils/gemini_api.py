import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def call_gemini_api(prompt: str) -> str | None:
    """Call Gemini API with a prompt and return generated text."""
    if not GEMINI_API_KEY:
        st.error("GEMINI_API_KEY is not configured.")
        return None

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    )
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.8,
            "topK": 40,
            "maxOutputTokens": 8192,
        },
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=45)
        if response.status_code != 200:
            st.error(f"Error calling Gemini API: {response.status_code} - {response.text}")
            return None

        payload = response.json()
        return payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        st.error("Unexpected response format from Gemini API.")
        return None
    except Exception as exc:
        st.error(f"Error during API call: {exc}")
        return None
