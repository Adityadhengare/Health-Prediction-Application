"""
AI Health-Risk Remarks Service
------------------------------
This module handles communication with the Google Gemini API using the official
`google-genai` SDK, with safe fallbacks, explicit source labeling, bounded timeouts,
and healthcheck diagnostics.

Key Safety & Assessment Requirements:
1. Load GEMINI_API_KEY from .env using python-dotenv. Never hardcode credentials.
2. Formulate cautious, probabilistic health-risk observations (NOT medical diagnoses).
3. Always append an explicit medical disclaimer.
4. Bounded HTTP Timeout: Enforce strict client timeouts (10-12s) to prevent application hangs.
5. Limit Gemini attempts to at most two verified candidate models.
6. If API calls fail or time out, gracefully return an explicitly labeled Local Rule-Based Fallback.
7. NEVER label fallback output as AI-generated. Explicitly tag output:
   - [Source: External AI API (Google Gemini - <model>)]
   - [Source: Local Rule-Based Engine (API unavailable/offline)]
"""

import os
from typing import Dict, Any, Tuple
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Standard medical disclaimer
MEDICAL_DISCLAIMER = (
    "DISCLAIMER: This automated observation is for informational and educational "
    "purposes only. It is not a clinical diagnosis or treatment recommendation. "
    "Always consult a qualified healthcare professional."
)

# Standard Google Gemini model identifiers (limited to 2 verified models)
# In google-genai SDK, types.HttpOptions.timeout is in milliseconds (12000 ms = 12 seconds)
API_TIMEOUT_MS = 12000.0

CANDIDATE_GEMINI_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]


def is_api_key_configured() -> bool:
    """Checks whether a valid, non-placeholder GEMINI_API_KEY is set in environment."""
    load_dotenv(override=True)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return bool(key) and key != "your_gemini_api_key_here"


def get_genai_client(api_key: str):
    """
    Returns a google.genai.Client instance configured with an explicit HTTP timeout.
    """
    from google import genai
    from google.genai import types

    # google-genai HttpOptions timeout is in milliseconds (12000ms = 12s)
    http_opts = types.HttpOptions(timeout=API_TIMEOUT_MS)
    return genai.Client(api_key=api_key, http_options=http_opts)


def test_gemini_connection() -> Tuple[bool, str]:
    """
    Safely tests the Gemini API connection with a minimal synthetic prompt and bounded timeout.
    Does NOT require or transmit any patient data, and NEVER prints/exposes the API key.
    
    Returns:
      (is_connected: bool, message: str)
    """
    if not is_api_key_configured():
        return False, "No valid GEMINI_API_KEY found in environment or .env file."

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    try:
        client = get_genai_client(api_key)
        
        last_error = None
        for model_name in CANDIDATE_GEMINI_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents="Health prediction test ping. Respond with: 'AI Connection OK'.",
                )
                if response and response.text:
                    return True, f"Successfully connected to Gemini API ({model_name})."
            except Exception as e:
                last_error = e
                # Check for rate limit or deadline exceed to avoid waiting for next model
                err_text = str(e)
                if "RESOURCE_EXHAUSTED" in err_text or "429" in err_text:
                    break
                continue
                
        raise last_error if last_error else RuntimeError("Failed to connect to any Gemini model.")
        
    except Exception as e:
        error_name = type(e).__name__
        err_str = str(e)
        if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
            clean_msg = "Google Gemini rejected the API key as invalid. Please check your key in Google AI Studio."
        elif "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
            clean_msg = "Gemini API quota exceeded (Rate limit 429). The app will automatically use local clinical fallback."
        elif "DEADLINE_EXCEEDED" in err_str or "ReadTimeout" in err_str or "Timeout" in error_name:
            clean_msg = "Gemini API request timed out (bounded 12s limit). Using local clinical fallback."
        else:
            clean_msg = f"{error_name}: {err_str[:120]}"
        return False, clean_msg


def generate_local_fallback_remarks(
    glucose: float, haemoglobin: float, cholesterol: float
) -> str:
    """
    Generates a deterministic, rule-based clinical observation when external AI API is unavailable.
    
    CRITICAL: This function is explicitly tagged as a local fallback and NEVER claimed to be AI.
    """
    observations = []

    # Glucose indicator
    if glucose > 200:
        observations.append(
            f"Blood Glucose ({glucose} mg/dL) is significantly elevated, indicating potential risk of hyperglycemia or impaired glucose regulation."
        )
    elif glucose > 140:
        observations.append(
            f"Blood Glucose ({glucose} mg/dL) is moderately elevated above standard fasting baselines."
        )
    elif glucose < 70:
        observations.append(
            f"Blood Glucose ({glucose} mg/dL) is below standard reference baselines, indicating potential hypoglycemia risk."
        )
    else:
        observations.append(
            f"Blood Glucose ({glucose} mg/dL) is within typical reference ranges."
        )

    # Haemoglobin indicator
    if haemoglobin < 10.0:
        observations.append(
            f"Haemoglobin ({haemoglobin} g/dL) is low, which may be associated with anemia."
        )
    elif haemoglobin < 12.0:
        observations.append(
            f"Haemoglobin ({haemoglobin} g/dL) is borderline low."
        )
    elif haemoglobin > 18.0:
        observations.append(
            f"Haemoglobin ({haemoglobin} g/dL) is elevated above standard adult reference limits."
        )
    else:
        observations.append(
            f"Haemoglobin ({haemoglobin} g/dL) is within typical adult reference boundaries."
        )

    # Cholesterol indicator
    if cholesterol >= 240:
        observations.append(
            f"Total Cholesterol ({cholesterol} mg/dL) is elevated, suggesting possible hypercholesterolemia or lipid imbalance."
        )
    elif cholesterol >= 200:
        observations.append(
            f"Total Cholesterol ({cholesterol} mg/dL) is borderline elevated."
        )
    else:
        observations.append(
            f"Total Cholesterol ({cholesterol} mg/dL) is within desirable reference levels."
        )

    summary = " ".join(observations)
    
    return (
        f"[Source: Local Rule-Based Engine (API unavailable/offline)]\n"
        f"{summary}\n\n"
        f"{MEDICAL_DISCLAIMER}"
    )


def generate_health_remarks(
    full_name: str,
    date_of_birth: str,
    glucose: float,
    haemoglobin: float,
    cholesterol: float,
) -> Tuple[str, str]:
    """
    Generates health-risk remarks by calling Google Gemini API or falling back gracefully.
    Guaranteed bounded execution (at most 2 models with 12s timeout each).
    
    Returns:
      (remarks_text: str, source_type: str)
      source_type is either 'EXTERNAL_AI' or 'LOCAL_FALLBACK'
    """
    if not is_api_key_configured():
        fallback_remark = generate_local_fallback_remarks(glucose, haemoglobin, cholesterol)
        return fallback_remark, "LOCAL_FALLBACK"

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    # Attempt external Google GenAI call with explicit bounded timeout
    try:
        client = get_genai_client(api_key)
        
        prompt = f"""
You are a health analytics assistant evaluating routine laboratory test metrics.
Patient Details:
- Name: {full_name}
- Date of Birth: {date_of_birth}
- Blood Glucose: {glucose} mg/dL
- Haemoglobin: {haemoglobin} g/dL
- Total Cholesterol: {cholesterol} mg/dL

Provide a cautious, informational assessment in 2-3 sentences:
1. Summarize any out-of-range metrics and note general health risk associations (e.g. hyperglycemia, anemia indicators, or elevated lipid profiles).
2. Use cautious, probabilistic language. Do NOT declare a confirmed medical diagnosis.
3. Keep the tone professional, objective, and empathetic.
"""
        response = None
        used_model = None
        last_err = None

        for model_name in CANDIDATE_GEMINI_MODELS:
            try:
                res = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if res and res.text:
                    response = res
                    used_model = model_name
                    break
            except Exception as e_mod:
                last_err = e_mod
                err_text = str(e_mod)
                # If rate-limited (429), break immediately to avoid waiting for next candidate
                if "RESOURCE_EXHAUSTED" in err_text or "429" in err_text:
                    break
                continue

        if response and response.text:
            cleaned_text = response.text.strip()
            ai_remark = (
                f"[Source: External AI API (Google Gemini - {used_model})]\n"
                f"{cleaned_text}\n\n"
                f"{MEDICAL_DISCLAIMER}"
            )
            return ai_remark, "EXTERNAL_AI"
        else:
            raise last_err if last_err else ValueError("Empty response received from Gemini API.")

    except Exception as e:
        # Gracefully handle missing keys, quota limits, timeouts, or network failures
        fallback_remark = generate_local_fallback_remarks(glucose, haemoglobin, cholesterol)
        error_type = type(e).__name__
        err_str = str(e)
        if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
            diag_reason = "Quota limit reached (Rate limit 429)"
        elif "DEADLINE_EXCEEDED" in err_str or "ReadTimeout" in err_str or "Timeout" in error_type:
            diag_reason = "API request timed out (bounded 12s limit)"
        else:
            diag_reason = f"{error_type}: {err_str[:80].replace(chr(10), ' ')}"
            
        diagnostic_note = f"\n(Note: External AI call reverted to local fallback due to: {diag_reason})"
        return fallback_remark + diagnostic_note, "LOCAL_FALLBACK"
