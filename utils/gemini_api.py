import requests
import streamlit as st

# Replace with your Gemini API key
GEMINI_API_KEY = "AIzaSyA3X6sZkGxAyobx2x-0yko1X0vfwqQkM5E"

def call_gemini_api(prompt):
    """
    Calls the Gemini API with the given prompt and returns the response.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, json=data, headers=headers)

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
