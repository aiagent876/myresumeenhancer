import os

import requests
import streamlit as st


def call_gemini_api(prompt):
    """
    Calls the Gemini API with the given prompt and returns the response.
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        st.error(
            "Missing Gemini API key. Please set GEMINI_API_KEY in your environment or .env file."
        )
        return None

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": gemini_api_key}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, params=params, json=data, headers=headers)

        if response.status_code == 200:
            try:
                # Parse and return the content
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            except KeyError:
                st.error("Unexpected response format from Gemini API.")
                return None
        else:
            st.error(f"API Error: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error calling Gemini API: {e}")
        return None
