import time

import requests

# Replace with your Gemini API key
GEMINI_API_KEY = "AIzaSyA3X6sZkGxAyobx2x-0yko1X0vfwqQkM5E"


def call_gemini_api(prompt):
    """
    Calls Gemini API and returns a structured status object.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    timeout_seconds = 30
    max_attempts = 4
    backoff_base_seconds = 1

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(url, json=data, headers=headers, timeout=timeout_seconds)

            if response.status_code in (429,) or 500 <= response.status_code < 600:
                if attempt < max_attempts:
                    time.sleep(backoff_base_seconds * (2 ** (attempt - 1)))
                    continue
                return {
                    "success": False,
                    "message": f"Gemini API returned transient error {response.status_code} after retries.",
                    "details": {
                        "status_code": response.status_code,
                        "response_text": response.text,
                        "attempts": attempt,
                    },
                }

            if response.status_code != 200:
                return {
                    "success": False,
                    "message": f"Gemini API request failed with status {response.status_code}.",
                    "details": {
                        "status_code": response.status_code,
                        "response_text": response.text,
                    },
                }

            try:
                payload = response.json()
            except ValueError:
                return {
                    "success": False,
                    "message": "Gemini API returned malformed JSON.",
                    "details": {
                        "status_code": response.status_code,
                        "response_text": response.text,
                    },
                }

            candidates = payload.get("candidates")
            if not isinstance(candidates, list) or not candidates:
                return {
                    "success": False,
                    "message": "Gemini API response is missing a valid 'candidates' field.",
                    "details": {"payload": payload},
                }

            try:
                text = candidates[0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError):
                return {
                    "success": False,
                    "message": "Gemini API response candidates are missing expected content text.",
                    "details": {"payload": payload},
                }

            return {
                "success": True,
                "message": "Gemini content generated successfully.",
                "details": {"text": text, "attempts": attempt},
            }

        except requests.exceptions.Timeout as e:
            if attempt < max_attempts:
                time.sleep(backoff_base_seconds * (2 ** (attempt - 1)))
                continue
            return {
                "success": False,
                "message": "Gemini API request timed out.",
                "details": {"error": str(e), "attempts": attempt},
            }
        except requests.exceptions.ConnectionError as e:
            if attempt < max_attempts:
                time.sleep(backoff_base_seconds * (2 ** (attempt - 1)))
                continue
            return {
                "success": False,
                "message": "Unable to connect to Gemini API.",
                "details": {"error": str(e), "attempts": attempt},
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": "Error during Gemini API request.",
                "details": {"error": str(e), "attempt": attempt},
            }
