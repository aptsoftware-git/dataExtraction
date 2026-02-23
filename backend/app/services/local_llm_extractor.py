import requests
import json

from app.config import OLLAMA_URL, LLM_MODEL
from app.utils.logger import log


SYSTEM_PROMPT = """
You are a Defence Intelligence Structured Data Extraction Engine.

Your task is to extract structured fields from intelligence report body text.

STRICT RULES:
- Do NOT hallucinate.
- Do NOT infer missing data.
- Do NOT assume unstated information.
- If a field is not explicitly present, return null.
- Return ONLY valid JSON.
- Do NOT include explanations.
- Do NOT include markdown.
- Output must strictly match the schema.

FIELD DEFINITIONS:

1. heading:
   - The heading is the FIRST line or FIRST sentence of the report.
   - It usually appears before the first period.
   - Extract it exactly as written.
   - Do NOT rewrite or summarize it.
   - Do NOT invent a new title.

2. input_summary:
   - A concise factual summary of the remaining text (excluding heading).
   - Maximum 3 lines.
   - Only include explicitly stated facts.

3. gen_area:
   - Extract only if clearly mentioned.

4. state:
   - Extract only if explicitly written.

5. district:
   - Extract only if explicitly written.

6. coordinates:
   - Extract only if exact numeric latitude/longitude appears.
   - Do NOT generate coordinates.

If a field is missing, return null.
Return strictly valid JSON only.
"""

# Log LLM failure only once
_llm_unavailable_logged = False


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
            timeout=30
        )

        if response.status_code != 200:
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

    except Exception:
        global _llm_unavailable_logged

        if not _llm_unavailable_logged:
            log("LLM", "LLM server not reachable. Using fallback.")
            _llm_unavailable_logged = True

        return fallback_summary(schema, body_text)


def fallback_summary(schema, body_text):
    schema["input_summary"] = body_text[:300]
    return schema


def _safe_json_parse(text: str) -> dict:
    if not text:
        raise RuntimeError("Empty response from LLM")

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise RuntimeError("Invalid JSON from LLM")

    return json.loads(text[start:end + 1])