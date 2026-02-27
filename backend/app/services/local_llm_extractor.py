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

Your task is to extract structured military intelligence data from a single isolated intelligence record.

You must extract EXACTLY the following 19 JSON fields:

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

-----------------------------------------
FIELD DEFINITIONS (STRICT MILITARY LOGIC)
-----------------------------------------

1. date:
Extract the DATE OF EVENT mentioned inside the narrative.
If multiple dates appear, select the date on which the event occurred.
Ignore report filing dates unless event date is missing.

2. fmn:
Higher formation (Corps/Division/Brigade) responsible for the region.
Extract ONLY if explicitly mentioned.

3. aor_lower_fmn:
Lower tactical formation (Sector/Brigade/Battalion AOR).
Extract ONLY if explicitly stated (e.g., AOR 255 BGB).

4. unit:
The specific battalion or regiment on ground (e.g., 4 AR, 54 BGD).
Do NOT confuse with agency.

5. agency:
The source of intelligence (e.g., SIB, PHQ, ARFIU, EW Bn, BMC, 221 Tech).
If present in header/table, extract exactly as written.

6. country:
Country where activity occurred (India, Myanmar etc.).
Infer ONLY if explicitly stated.

7. state:
Indian state explicitly mentioned (Nagaland, Manipur, Arunachal Pradesh etc.).

8. district:
Administrative district explicitly mentioned.

9. gen_area:
General area, village, town, landmark, or broad locality.

10. gp:
Insurgent or militant group (e.g., NSCN(IM), TIRG, NACT, PUBS, TRTS).

11. heading:
Short operational title derived from the first phrase of the report.
Do NOT invent creative language.
Keep factual and concise.

12. input_summary:
Concise factual summary.
Preserve operational tone.
Do NOT speculate.
Do NOT exaggerate.
Do NOT add intelligence assessment.
Do NOT repeat markdown formatting.

13. coordinates:
Extract latitude/longitude or grid reference ONLY if explicitly stated.

14. engagement_type_reasoned:
Must be ONE of:
Movement, Arrest, Recovery, Offensive, Meeting,
Explosion, IED, Extortion, Surrender,
Subversive Activity, Intelligence Input,
Firefight, Warning, Political Activity

Select based strictly on event type:
- Extortion demand → Extortion
- Desertion/Defection → Surrender
- Inter-faction clash → Firefight
- Security warning → Warning
- Information sharing → Intelligence Input
- Arrest by group → Arrest
- Combat engagement → Firefight

If unclear → null.

15–16. cadres_min / cadres_max:
Extract ONLY numbers referring to militants/cadres.
Ignore:
- Monetary amounts (₹2 lakh)
- Truck counts
- Time (1200 hrs)
If a range (7–8 leaders):
min=7
max=8

17. leader:
Extract named leader or self-styled commander (SS prefix if present).
Include rank if explicitly mentioned.

18. weapons:
List weapons explicitly mentioned (AK, pistol, grenade, RPG etc.).
Do NOT infer.

19. ammunition:
Extract ammunition quantity and type explicitly stated.
Do NOT infer.

-----------------------------------------
STRICT RULES
-----------------------------------------

- Extract ONLY explicitly stated information.
- Do NOT infer missing data.
- Do NOT assume.
- Do NOT merge information from other records.
- Treat each input as isolated.
- If a field is not clearly present → return null.
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