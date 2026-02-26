import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from app.utils.logger import log

# ==========================================
# Load Environment Variables
# ==========================================

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "35"))
LLM_MAX_WORKERS = int(os.getenv("LLM_MAX_WORKERS", "4"))
LLM_MAX_TEXT_LENGTH = int(os.getenv("LLM_MAX_TEXT_LENGTH", "2000"))

if not OLLAMA_URL:
    raise ValueError("OLLAMA_URL not set in .env")

if not LLM_MODEL:
    raise ValueError("LLM_MODEL not set in .env")

# Persistent session
session = requests.Session()

# ==========================================
# SYSTEM PROMPT
# ==========================================

SYSTEM_PROMPT = """
You are a Defence Intelligence Structured Data Extraction Engine.

You must extract structured military intelligence data into EXACTLY the following 19 JSON fields:

date,
fmn,
aor_lower_fmn,
unit,
agency,
country,
state,
district,
gen_area,
gp,
heading,
input_summary,
coordinates,
engagement_type_reasoned,
cadres_min,
cadres_max,
leader,
weapons,
ammunition


FIELD DEFINITIONS:

1. date:
The date the intelligence event occurred or was reported.

2. fmn:
Higher formation (Corps / Division / Brigade) responsible for the area.

3. aor_lower_fmn:
Lower tactical formation responsible for the specific Area of Responsibility.

4. unit:
Specific battalion or regiment collecting the input (e.g., 4 AR).

5. agency:
Intelligence source (SIB, PHQ, ARFIU, EW Bn, etc.).

6. country:
Country where activity occurred (India / Myanmar etc.).

7. state:
Indian state involved (Nagaland, Manipur, Arunachal Pradesh etc.).

8. district:
Administrative district of activity.

9. gen_area:
General vicinity or landmark where event occurred.

10. gp:
Militant / insurgent group (NSCN(IM), NSCN(K-YA), ULFA(I) etc.).

11. heading:
Generate a short operational title (3–8 words).
It must summarize the primary activity.
Do NOT copy the first sentence blindly.

12. input_summary:
Provide a clear factual summary of the event.
Do not repeat markdown formatting.
Keep it concise but complete.

13. coordinates:
Grid reference or latitude/longitude if explicitly stated.

14. engagement_type_reasoned:
Must be ONE of:
Movement, Arrest, Recovery, Offensive, Meeting,
Explosion, IED, Extortion, Surrender,
Subversive Activity, Intelligence Input,
Firefight, Warning, Political Activity
If unclear → null.

15–16. cadres_min / cadres_max:
Extract ONLY numbers directly referring to militants/cadres.
If range 30–40 → min=30, max=40.
Do NOT mix unrelated numbers (₹10 lakh, 1000 troops etc.).

17. leader:
Named leader or self-styled commander mentioned.

18. weapons:
Weapons explicitly mentioned.

19. ammunition:
Ammunition details explicitly mentioned.


STRICT RULES:
- Extract ONLY explicitly stated information.
- Do NOT infer.
- Do NOT hallucinate.
- If a field is missing → return null.
- Return ONLY valid JSON.
- No explanations.
"""

# ==========================================
# JSON Schema Template
# ==========================================

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

# ==========================================
# Single Block Extraction
# ==========================================

def extract_semantic_fields(text: str) -> dict:

    if not text or len(text.strip()) < 10:
        return SCHEMA.copy()

    if len(text) > LLM_MAX_TEXT_LENGTH:
        text = text[:LLM_MAX_TEXT_LENGTH]

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""
Extract structured military intelligence fields from the following report:

{text}

Return ONLY valid JSON with the 19 required fields.
"""
            }
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

        if response.status_code != 200:
            log("LLM_ERROR", f"Status {response.status_code}")
            fallback = SCHEMA.copy()
            fallback["input_summary"] = text[:300]
            return fallback

        raw_output = response.json().get("message", {}).get("content", "")

        if not raw_output:
            log("LLM_ERROR", "Empty response")
            fallback = SCHEMA.copy()
            fallback["input_summary"] = text[:300]
            return fallback

        # Extract JSON safely
        start = raw_output.find("{")
        end = raw_output.rfind("}")

        if start == -1 or end == -1:
            log("LLM_ERROR", "Invalid JSON format from LLM")
            fallback = SCHEMA.copy()
            fallback["input_summary"] = text[:300]
            return fallback

        parsed = json.loads(raw_output[start:end + 1])

        # Ensure all keys exist
        for key in SCHEMA:
            parsed.setdefault(key, None)

        return parsed

    except Exception as e:
        log("LLM_ERROR", str(e))
        fallback = SCHEMA.copy()
        fallback["input_summary"] = text[:300]
        return fallback


# ==========================================
# Parallel Processing
# ==========================================

def extract_multiple_blocks_parallel(blocks: list) -> list:

    if not blocks:
        return []

    results = [None] * len(blocks)

    log("PROCESS", f"Sending {len(blocks)} blocks to LLM")

    with ThreadPoolExecutor(max_workers=LLM_MAX_WORKERS) as executor:

        futures = {
            executor.submit(extract_semantic_fields, block): i
            for i, block in enumerate(blocks)
        }

        for future in as_completed(futures):
            idx = futures[future]
            results[idx] = future.result()

    return results