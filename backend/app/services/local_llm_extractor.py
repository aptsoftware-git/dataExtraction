import requests
import json

from app.config import OLLAMA_URL, LLM_MODEL
from app.utils.logger import log


SYSTEM_PROMPT = """
You are a Defence Intelligence Data Extraction Analyst.

Extract structured semantic fields from the BODY TEXT.

Rules:
- Do NOT hallucinate.
- Do NOT infer missing details.
- ALWAYS generate input_summary if body text exists.
- Keep summary factual and concise (max 3 lines).
- Return ONLY valid JSON.
"""


def extract_semantic_fields(body_text: str) -> dict:
    log("LLM", "Extracting semantic fields")

    schema = {
        "heading": None,
        "input_summary": None,
        "gen_area": None,
        "state": None,
        "district": None,
        "coordinates": None
    }

    if not body_text or len(body_text.strip()) < 10:
        return schema

    user_prompt = f"""
Extract the following fields.

SCHEMA:
{json.dumps(schema, indent=2)}

BODY TEXT:
\"\"\"
{body_text}
\"\"\"

Return strictly valid JSON.
"""

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "temperature": 0
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=180
        )

        if response.status_code != 200:
            log("LLM", f"Model error → {response.text}")
            return fallback_summary(schema, body_text)

        response_json = response.json()
        raw_output = response_json.get("message", {}).get("content")

        parsed = _safe_json_parse(raw_output)

        for key in schema:
            parsed.setdefault(key, None)

        if not parsed.get("input_summary"):
            parsed["input_summary"] = body_text[:300]

        log("LLM", "LLM semantic extraction completed")
        return parsed

    except Exception as e:
        log("LLM", f"LLM crashed → {e}")
        return fallback_summary(schema, body_text)


def fallback_summary(schema, body_text):
    schema["input_summary"] = body_text[:300]
    return schema


def _safe_json_parse(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise RuntimeError("Invalid JSON from LLM")

    return json.loads(text[start:end + 1])
