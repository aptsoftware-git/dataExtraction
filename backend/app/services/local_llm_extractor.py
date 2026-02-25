import requests
import json
import os
from dotenv import load_dotenv

from app.utils.logger import log

# Load environment variables
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")
LLM_MODEL = os.getenv("LLM_MODEL")


SYSTEM_PROMPT = """
You are a Defence Intelligence Structured Data Extraction Engine.

Your task is to extract structured information from intelligence narrative text.

STRICT RULES:

- Do NOT hallucinate.
- Do NOT infer missing information.
- Do NOT rewrite facts.
- Only extract what is explicitly stated.
- If a field is not clearly present, return null.
- Return ONLY valid JSON.
- No explanations.
- No markdown.
- No extra text.
- The output JSON must match the schema keys exactly. Do not add or remove keys.

FIELD DEFINITIONS:

1. heading:
   - Extract the first sentence or first titled line exactly as written.
   - Do NOT summarize.

2. input_summary:
   - Provide a concise factual summary (max 3 lines).
   - Exclude the heading.
   - Only include explicitly stated facts.

3. gen_area:
   - Extract only if clearly mentioned.

4. state:
   - Extract only if explicitly mentioned.

5. district:
   - Extract only if explicitly mentioned.

6. coordinates:
   - Extract only if exact numeric latitude/longitude appears.
   - Do NOT generate coordinates.

OUTPUT FORMAT:

Return strictly valid JSON with this structure:

{
  "heading": string or null,
  "input_summary": string or null,
  "gen_area": string or null,
  "state": string or null,
  "district": string or null,
  "coordinates": string or null
}

If any field is not present, set it to null.

Return JSON only.
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
Extract structured fields strictly in JSON format.

SCHEMA:
{json.dumps(schema, indent=2)}

TEXT:
\"\"\"
{body_text}
\"\"\"

Return ONLY valid JSON.
Do not add any commentary.
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