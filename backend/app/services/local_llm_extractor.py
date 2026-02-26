import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from app.utils.logger import log

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "35"))
LLM_MAX_WORKERS = int(os.getenv("LLM_MAX_WORKERS", "4"))
LLM_MAX_TEXT_LENGTH = int(os.getenv("LLM_MAX_TEXT_LENGTH", "2000"))

if not OLLAMA_URL:
    raise ValueError("OLLAMA_URL not set in .env")

session = requests.Session()

SYSTEM_PROMPT = """
You are a Defence Intelligence Structured Data Extraction Engine.

Extract EXACTLY these 19 fields as JSON:

date, fmn, aor_lower_fmn, unit, agency, country, state, district,
gen_area, gp, heading, input_summary, coordinates,
engagement_type_reasoned, cadres_min, cadres_max,
leader, weapons, ammunition

STRICT RULES:
- Extract only explicitly stated data
- Do not infer
- Use null if missing
- Return only valid JSON
"""

SCHEMA = {
    "date": None,
    "fmn": None,
    "aor_lower_fmn": None,
    "unit": None,
    "agency": None,
    "country": None,
    "state": None,
    "district": None,
    "gen_area": None,
    "gp": None,
    "heading": None,
    "input_summary": None,
    "coordinates": None,
    "engagement_type_reasoned": None,
    "cadres_min": None,
    "cadres_max": None,
    "leader": None,
    "weapons": None,
    "ammunition": None
}


def extract_semantic_fields(text: str) -> dict:

    if len(text) > LLM_MAX_TEXT_LENGTH:
        text = text[:LLM_MAX_TEXT_LENGTH]

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": 4096,
            "num_predict": 700
        }
    }

    try:
        response = session.post(
            OLLAMA_URL,
            json=payload,
            timeout=LLM_TIMEOUT
        )

        raw = response.json().get("message", {}).get("content", "")

        start = raw.find("{")
        end = raw.rfind("}")

        if start == -1 or end == -1:
            return SCHEMA.copy()

        parsed = json.loads(raw[start:end + 1])

        for key in SCHEMA:
            parsed.setdefault(key, None)

        return parsed

    except Exception as e:
        log("LLM_ERROR", str(e))
        fallback = SCHEMA.copy()
        fallback["input_summary"] = text[:300]
        return fallback


def extract_multiple_blocks_parallel(blocks: list) -> list:

    results = [None] * len(blocks)

    with ThreadPoolExecutor(max_workers=LLM_MAX_WORKERS) as executor:
        futures = {
            executor.submit(extract_semantic_fields, block): i
            for i, block in enumerate(blocks)
        }

        for future in as_completed(futures):
            idx = futures[future]
            results[idx] = future.result()

    return results