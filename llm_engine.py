import os
import json
import logging
import re
from groq import Groq
from dotenv import load_dotenv

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not found in environment variables. LLM calls will return fallback responses.")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

MODEL = "llama-3.1-8b-instant"

# Required keys in the LLM response
REQUIRED_KEYS = {"risk_summary", "key_anomalies", "regulatory_concerns", "recommended_action", "confidence"}

FALLBACK_RESPONSE = {
    "risk_summary": "LLM output invalid or unavailable.",
    "key_anomalies": [],
    "regulatory_concerns": [],
    "recommended_action": "escalate",
    "confidence": 0.0
}


# ---------------------------------------------------
# LLM OUTPUT CLEANING
# ---------------------------------------------------
def clean_llm_output(output: str) -> str:
    """
    Strips markdown code-block wrappers and extracts the JSON object.
    """
    output = output.strip()

    # Remove ```json ... ``` or ``` ... ``` wrappers
    output = re.sub(r"^```(?:json)?\s*\n?", "", output)
    output = re.sub(r"\n?```\s*$", "", output)

    # Extract the outermost JSON object
    first_brace = output.find("{")
    last_brace = output.rfind("}")

    if first_brace != -1 and last_brace != -1:
        output = output[first_brace:last_brace + 1]

    return output.strip()


def validate_response(parsed: dict) -> dict:
    """
    Ensures all required keys exist in the parsed LLM response.
    Returns FALLBACK_RESPONSE if validation fails.
    """
    if not isinstance(parsed, dict):
        logger.warning("LLM response is not a dict, returning fallback.")
        return FALLBACK_RESPONSE.copy()

    missing = REQUIRED_KEYS - set(parsed.keys())
    if missing:
        logger.warning("LLM response missing keys %s, returning fallback.", missing)
        return FALLBACK_RESPONSE.copy()

    return parsed


# ---------------------------------------------------
# MAIN LLM FUNCTION
# ---------------------------------------------------
def generate_risk_report(context_dict: dict) -> dict:
    """
    Sends structured transaction context to Groq
    and returns a validated JSON risk assessment.
    """
    if client is None:
        logger.error("Groq client not initialized (missing API key).")
        return FALLBACK_RESPONSE.copy()

    prompt = f"""
You are a financial compliance AI system.

Return STRICT JSON only. No explanation outside JSON.

Use exactly this schema:

{{
  "risk_summary": "string",
  "key_anomalies": ["string"],
  "regulatory_concerns": ["string"],
  "recommended_action": "approve | escalate | freeze",
  "confidence": float_between_0_and_1
}}

Context:
{json.dumps(context_dict, indent=2)}

Decision Guidance:
- If risk_score > 0.8 → bias toward "freeze"
- If 0.5 <= risk_score <= 0.8 → "escalate"
- If risk_score < 0.5 → "approve"
- When uncertain, escalate.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You ONLY return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        raw_output = response.choices[0].message.content
        logger.debug("Raw LLM output: %s", raw_output)

        cleaned = clean_llm_output(raw_output)
        parsed = json.loads(cleaned)
        return validate_response(parsed)

    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM JSON: %s", e)
        return FALLBACK_RESPONSE.copy()

    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return FALLBACK_RESPONSE.copy()


# ---------------------------------------------------
# TEST BLOCK
# ---------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    sample_context = {
        "transaction": {
            "transaction_id": "test_1",
            "amount": 12000,
            "country": "Russia",
            "device_id": "new_device",
            "timestamp": "2026-03-01T10:15:00"
        },
        "behavioral_metrics": {
            "amount_zscore": 4.2,
            "country_change_flag": 1,
            "device_change_flag": 1,
            "burst_flag": 0
        },
        "risk_score": 0.91
    }

    result = generate_risk_report(sample_context)

    print("\nFINAL PARSED RESULT:")
    print(json.dumps(result, indent=2))