import requests
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

from app.utils.logger import log

# Create a persistent session for connection pooling
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=10,
    max_retries=1
)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Load environment variables
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-r1:32b")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "15"))
LLM_MAX_WORKERS = int(os.getenv("LLM_MAX_WORKERS", "6"))
LLM_MAX_TEXT_LENGTH = int(os.getenv("LLM_MAX_TEXT_LENGTH", "1500"))
LLM_SKIP_MAPPING = os.getenv("LLM_SKIP_MAPPING", "true").lower() == "true"


SYSTEM_PROMPT = """You are a military intelligence data extraction system. Extract information from reports into structured JSON.

FIELDS TO EXTRACT:
1. date: Event date (format: DD-MMM-YY, e.g., "15-Jan-24")
2. fmn: Formation name (e.g., "3 Corps", "Spear Corps", "XVI Corps")
3. aor_lower_fmn: Lower formation (e.g., "21 Sector", "HQ IGAR(S)")
4. unit: Unit designation (e.g., "4 AR", "23 Assam Rifles", "9 Dogra")
5. agency: Intelligence source (e.g., "SIB", "PHQ", "ARFIU", "EW Bn")
6. country: Country name (e.g., "India", "Myanmar")
7. state: State name (e.g., "Nagaland", "Manipur", "Arunachal Pradesh")
8. district: District name (e.g., "Mon", "Dimapur", "Longleng")
9. gen_area: General area description (e.g., "Near Yongnyah village")
10. gp: Militant group (e.g., "NSCN(IM)", "NSCN(K-YA)", "ULFA(I)", "PLA")
11. heading: Brief title (e.g., "Movement of Cadres", "Arms Recovery")
12. input_summary: Full description of the incident
13. coordinates: Location (e.g., "N26°45' E94°30'", "Grid 1234 5678")
14. engagement_type_reasoned: Event type (e.g., "Encounter", "Arrest", "Recovery", "Surrender", "Firefight", "IED blast")
15. cadres_min: Minimum militants count (number only)
16. cadres_max: Maximum militants count (number only)
17. leader: Leader name (e.g., "SS Maj Konyak", "Capt Wangsa")
18. weapons: Weapons list (e.g., "2 AK-47, 1 Pistol")
19. ammunition: Ammunition (e.g., "50 rounds", "2 grenades")

EXAMPLE:
Input: "On 15-Jan-24, troops of 23 Assam Rifles apprehended 2 NSCN(IM) cadres near Mon town, Nagaland. Recovered 1 AK-47 rifle."
Output:
{
  "date": "15-Jan-24",
  "unit": "23 Assam Rifles",
  "state": "Nagaland",
  "district": "Mon",
  "gp": "NSCN(IM)",
  "engagement_type_reasoned": "Arrest",
  "cadres_min": 2,
  "cadres_max": 2,
  "weapons": "1 AK-47",
  "heading": "Arrest of NSCN(IM) cadres",
  "input_summary": "Troops of 23 Assam Rifles apprehended 2 NSCN(IM) cadres near Mon town. Recovered 1 AK-47 rifle."
}

RULES:
- Extract ONLY information stated in text
- Use null for missing fields
- Return valid JSON only (no extra text)
- Be precise with numbers and names"""

# Log LLM failure only once
_llm_unavailable_logged = False


def extract_semantic_fields(body_text: str) -> dict:
    schema = {
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

    if not body_text or len(body_text.strip()) < 10:
        return schema

    # Truncate very long texts to optimize processing time
    if len(body_text) > LLM_MAX_TEXT_LENGTH:
        body_text = body_text[:LLM_MAX_TEXT_LENGTH]

    # Ultra-concise prompt for speed
    # For qwen2.5-coder, direct and structured prompt works best
    is_reasoning_model = "deepseek-r1" in LLM_MODEL.lower() or "r1" in LLM_MODEL.lower()
    is_coder_model = "coder" in LLM_MODEL.lower() or "qwen" in LLM_MODEL.lower()
    is_llama3_small = "llama3.1:8b" in LLM_MODEL.lower() or "llama3:8b" in LLM_MODEL.lower()
    
    if is_reasoning_model:
        user_prompt = f"""Answer DIRECTLY with JSON only. No thinking, no explanation.

Extract fields: {json.dumps(schema)}

Text: {body_text}"""
    elif is_llama3_small:
        # Optimized for llama3.1:8b - needs clear structure with examples
        user_prompt = f"""Extract military intelligence to JSON. Follow the system examples.

FIELDS: date, fmn, aor_lower_fmn, unit, agency, country, state, district, gen_area, gp, heading, input_summary, coordinates, engagement_type_reasoned, cadres_min, cadres_max, leader, weapons, ammunition

TEXT:
{body_text}

JSON OUTPUT (use null for missing fields):"""
    elif is_coder_model:
        # Optimized for qwen2.5-coder:32b - structured schema-driven extraction
        user_prompt = f"""Extract military intelligence from the text into the following JSON schema. Follow the system examples for field formats.

TARGET SCHEMA:
{json.dumps(schema, indent=2)}

SOURCE TEXT:
{body_text}

Return only valid JSON with the schema fields. Use null for missing data:"""
    else:
        user_prompt = f"""Extract: {json.dumps(schema)}\nFrom: {body_text}"""
    
    # Model-specific optimizations
    if is_reasoning_model:
        # Optimized for reasoning models (deepseek-r1)
        ollama_options = {
            "num_ctx": 2048,
            "num_predict": 400,
            "top_k": 10,
            "top_p": 0.95,
            "num_thread": 8,
            "repeat_penalty": 1.0,
            "temperature": 0.1
        }
    elif is_llama3_small:
        # Optimized for llama3.1:8b - balanced for speed and accuracy
        ollama_options = {
            "num_ctx": 3072,         # Good context for 19 fields
            "num_predict": 512,      # Enough tokens for all fields
            "top_k": 40,
            "top_p": 0.9,
            "num_thread": 6,
            "repeat_penalty": 1.1,
            "temperature": 0.2       # Balanced creativity
        }
    elif is_coder_model or is_llama3_70b:
        # Optimized for qwen2.5-coder:32b and similar coder models
        # Coder models excel at structured data extraction with technical terminology
        ollama_options = {
            "num_ctx": 4096,         # Large context for complex schemas
            "num_predict": 650,      # Sufficient tokens for all 19 fields with military terms
            "top_k": 40,
            "top_p": 0.95,
            "num_thread": 8,
            "repeat_penalty": 1.05,
            "temperature": 0.1       # Low temp for deterministic extraction
        }
    else:
        # Optimized for general models (mistral, etc)
        ollama_options = {
            "num_ctx": 2048,
            "num_predict": 400,
            "top_k": 20,
            "top_p": 0.9,
            "num_thread": 8,
            "repeat_penalty": 1.1
        }
    
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "temperature": 0,
        "options": ollama_options
    }

    try:
        start_time = time.time()
        response = session.post(
            OLLAMA_URL,
            json=payload,
            timeout=LLM_TIMEOUT
        )
        elapsed_time = time.time() - start_time
        
        if response.status_code != 200:
            log("LLM", f"ERROR: Status {response.status_code}")
            return fallback_summary(schema, body_text)

        response_json = response.json()
        raw_output = response_json.get("message", {}).get("content")
        
        if not raw_output:
            log("LLM", "ERROR: Empty response from LLM")
            return fallback_summary(schema, body_text)

        parsed = _safe_json_parse(raw_output)
        
        for key in schema:
            parsed.setdefault(key, None)

        if not parsed.get("input_summary"):
            parsed["input_summary"] = body_text[:300]
        
        # Log successful extraction for debugging
        extracted_count = sum(1 for v in parsed.values() if v is not None)
        if extracted_count < 3:  # Less than 3 fields extracted
            log("LLM", f"WARNING: Only {extracted_count} fields extracted")

        return parsed

    except (json.JSONDecodeError, RuntimeError) as e:
        log("LLM", f"JSON Parse Error: {str(e)[:100]}")
        return fallback_summary(schema, body_text)

    except requests.exceptions.ConnectionError as e:
        global _llm_unavailable_logged
        if not _llm_unavailable_logged:
            log("LLM", "✗ LLM server not reachable. Using fallback.")
            _llm_unavailable_logged = True
        return fallback_summary(schema, body_text)
    
    except requests.exceptions.Timeout as e:
        log("LLM", f"TIMEOUT after {LLM_TIMEOUT}s")
        return fallback_summary(schema, body_text)
    
    except Exception as e:
        log("LLM", f"Unexpected Error: {type(e).__name__}: {str(e)[:100]}")
        return fallback_summary(schema, body_text)


def fallback_summary(schema, body_text):
    schema["input_summary"] = body_text[:300]
    return schema


def extract_multiple_blocks_parallel(blocks: list, max_workers: int = None) -> list:
    """
    Process multiple text blocks in parallel using ThreadPoolExecutor.
    """
    if not blocks:
        return []
    
    if max_workers is None:
        max_workers = LLM_MAX_WORKERS
    
    is_reasoning = "deepseek-r1" in LLM_MODEL.lower() or "r1" in LLM_MODEL.lower()
    is_coder = "coder" in LLM_MODEL.lower() or "qwen" in LLM_MODEL.lower()
    
    if is_coder:
        model_type = "CODER"
    elif is_reasoning:
        model_type = "REASONING"
    else:
        model_type = "STANDARD"
    
    log("LLM", f"Processing {len(blocks)} blocks with {max_workers} workers [{model_type}: {LLM_MODEL}]")
    
    start_time = time.time()
    results = [None] * len(blocks)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(extract_semantic_fields, block): idx 
            for idx, block in enumerate(blocks)
        }
        
        completed = 0
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                results[idx] = future.result()
                completed += 1
                if completed % 5 == 0 or completed == len(blocks):
                    log("LLM", f"Progress: {completed}/{len(blocks)} blocks")
            except Exception as e:
                results[idx] = {
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
                    "input_summary": blocks[idx][:300] if idx < len(blocks) else None,
                    "coordinates": None,
                    "engagement_type_reasoned": None,
                    "cadres_min": None,
                    "cadres_max": None,
                    "leader": None,
                    "weapons": None,
                    "ammunition": None
                }
    
    elapsed = time.time() - start_time
    log("LLM", f"✓ Completed in {elapsed:.1f}s (avg: {elapsed/len(blocks):.2f}s/block)")
    
    return results


def _safe_json_parse(text: str) -> dict:
    if not text:
        raise RuntimeError("Empty response from LLM")

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise RuntimeError("Invalid JSON from LLM")

    return json.loads(text[start:end + 1])