import re

# =========================================================
# CONSTANTS
# =========================================================

STATE_TO_COUNTRY = {
    "Assam": "India",
    "Manipur": "India",
    "Nagaland": "India",
    "Arunachal Pradesh": "India",
    "Uttarakhand": "India",
    "Uttar Pradesh": "India",
    "Madhya Pradesh": "India",
    "Jammu And Kashmir": "India",
    "West Bengal": "India",
    "Chhattisgarh": "India"
}

KNOWN_DISTRICTS = [
    "Tinsukia", "Namsai", "Dimapur", "Chumukedima",
    "Mon", "Longleng", "Tengnoupal", "Pherzawl",
    "Noney", "Changlang", "KPI", "CCpur",
    "Thoubal", "Imphal", "Langol"
]

WEAPON_MAP = {
    "rocket-propelled gren": "RPG",
    "rpg": "RPG",
    "gren": "GRENADE",
    "grenade": "GRENADE",
    "sa fire": "SA",
    "ak-47": "AK-47",
    "lmg": "LMG",
    "ied": "IED",
    "rifle": "RIFLE"
}

EVENT_PRIORITY = [
    ("standoff firing", "Standoff Firing"),
    ("ablaze", "Ablaze/ Conflict"),
    ("burn", "Ablaze/ Conflict"),
    ("presence", "Presence of Cadres"),
    ("infilt", "Infiltration"),
    ("movement of cadres", "Movement of Cadres"),
    ("mov of cadres", "Movement of Cadres"),
    ("mov", "Movement of Cadres"),
    ("meeting", "Meeting"),
    ("mtg", "Meeting"),
    ("plg", "Planning"),
    ("planning", "Planning"),
    ("attack", "Firefight"),
    ("firing", "Firefight"),
    ("rpg", "Firefight"),
    ("grenade", "Firefight")
]

# =========================================================
# SOURCE PARSING (AGENCY, AOR, UNIT)
# =========================================================

def extract_source_fields(text):
    agency = None
    aor = None
    unit = None

    source_match = re.search(r'\(Source-\s*(.*?)\)', text)
    if source_match:
        source_text = source_match.group(1)

        parts = [p.strip() for p in source_text.split(",")]

        if len(parts) > 0:
            agency = parts[0]

        for part in parts:
            if "AOR" in part:
                aor = part.strip()
            if "Unit" in part:
                unit = part.replace("Unit", "").strip()

    return agency, aor, unit


# =========================================================
# FMN DETECTION
# =========================================================

def extract_fmn(text):
    t = text.lower()

    if "cob" in t:
        return "COB"
    if "camp" in t:
        return "Camp"
    if "unit" in t:
        return "Unit"
    if "post" in t:
        return "Post"

    return None


# =========================================================
# GP EXTRACTION (MULTI DETECTION + PRIORITY)
# =========================================================

def extract_gp(text):
    matches = re.findall(r'\b[A-Z]{3,6}\b', text)

    blacklist = {"AOR", "DIST", "UNIT", "GEN", "LOC"}

    candidates = [m for m in matches if m not in blacklist]

    if not candidates:
        return None

    # Return most frequent candidate
    return max(set(candidates), key=candidates.count)


# =========================================================
# STATE & DISTRICT
# =========================================================

def extract_state(text):
    for state in STATE_TO_COUNTRY:
        if state.lower() in text.lower():
            return state
    return None


def extract_district(text):
    districts_found = []

    for d in KNOWN_DISTRICTS:
        if d.lower() in text.lower():
            districts_found.append(d)

    if districts_found:
        return " / ".join(sorted(set(districts_found)))

    match = re.search(r'([A-Z][a-zA-Z]+)\s+(Dist|District)', text)
    if match:
        return match.group(1)

    return None


# =========================================================
# GENERAL AREA
# =========================================================

def extract_gen_area(text):
    match = re.search(r'gen\s*A\s*([A-Za-z\s&]+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


# =========================================================
# LEADER EXTRACTION (ENHANCED)
# =========================================================

def extract_leaders(text):

    # 1️⃣ Led by (highest priority)
    led_match = re.search(
        r'led by\s+(?:a\s+)?(SS\s+(?:Lt|Maj|Capt|Col|Gen|Sgt(?:\s+Maj)?)(?:\s+[A-Z][a-z]+)*)',
        text,
        re.IGNORECASE
    )
    if led_match:
        return led_match.group(1).strip()

    # 2️⃣ Chaired by
    chaired_match = re.search(
        r'chaired by\s+(SS\s+(?:Lt|Maj|Capt|Col|Gen|Sgt(?:\s+Maj)?)(?:\s+[A-Z][a-z]+)*)',
        text,
        re.IGNORECASE
    )
    if chaired_match:
        return chaired_match.group(1).strip()

    # 3️⃣ Headed by
    headed_match = re.search(
        r'headed by\s+(SS\s+(?:Lt|Maj|Capt|Col|Gen|Sgt(?:\s+Maj)?)(?:\s+[A-Z][a-z]+)*)',
        text,
        re.IGNORECASE
    )
    if headed_match:
        return headed_match.group(1).strip()

    # 4️⃣ Named pattern (MS Karabi Hati type)
    named_match = re.search(
        r'named\s+([A-Z]{1,3}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        text
    )
    if named_match:
        return named_match.group(1).strip()

    # 5️⃣ Fallback rank-based extraction (first occurrence only)
    rank_match = re.search(
        r'\bSS\s+(?:Lt|Maj|Capt|Col|Gen|Sgt(?:\s+Maj)?)(?:\s+[A-Z][a-z]+)*',
        text
    )
    if rank_match:
        return rank_match.group(0).strip()

    return None
# =========================================================
# ADVANCED CADRE PRIORITIZATION
# =========================================================

def extract_cadre_numbers(text):
    text_lower = text.lower()

    strengths = []

    # Range (10-15)
    range_matches = re.findall(r'(\d+)\s*[-/]\s*(\d+)\s*(?:x\s*)?(?:cadres?)', text_lower)
    for m in range_matches:
        strengths.append((int(m[0]), int(m[1])))

    # Approx X
    approx_matches = re.findall(r'approx\s*(\d+)\s*x', text_lower)
    for m in approx_matches:
        strengths.append((int(m), int(m)))

    # X cadres
    x_matches = re.findall(r'(\d+)\s*x\s*(?:cadres?)', text_lower)
    for m in x_matches:
        strengths.append((int(m), int(m)))

    # Normal
    normal_matches = re.findall(r'(\d+)\s+(?:cadres?|militants?)', text_lower)
    for m in normal_matches:
        strengths.append((int(m), int(m)))

    if not strengths:
        return None, None
    # choose strength with largest max value
    best = max(strengths, key=lambda x: x[1])
    return best


# =========================================================
# EVENT CLASSIFICATION (HIERARCHICAL)
# =========================================================

def detect_event_type(text):
    t = text.lower()

    for keyword, label in EVENT_PRIORITY:
        if keyword in t:
            return label

    return "IFC"


# =========================================================
# WEAPON NORMALIZATION
# =========================================================

def extract_weapons(text):
    t = text.lower()
    found = set()

    for key, val in WEAPON_MAP.items():
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, t):
            found.add(val)

    return ", ".join(sorted(found)) if found else None

# =========================================================
# AMMUNITION
# =========================================================

def extract_ammunition(text):
    matches = re.findall(r'(\d+)\s*x\s*(?:rpg\s*)?(?:rounds?|rds)', text.lower())
    if matches:
        return str(max(int(m) for m in matches))
    return None


# =========================================================
# APPLY MAPPING (MASTER ENGINE)
# =========================================================

def apply_mapping(data: dict, body_text: str) -> dict:

    # Source parsing
    agency, aor, unit = extract_source_fields(body_text)

    if agency:
        data["agency"] = agency
    if aor:
        data["aor_lower_fmn"] = aor
    if unit:
        data["unit"] = unit

    # Structural extraction
    data["fmn"] = extract_fmn(body_text)

    gp = extract_gp(body_text)
    if gp:
        data["gp"] = gp

    data["state"] = extract_state(body_text)
    data["district"] = extract_district(body_text)
    data["gen_area"] = extract_gen_area(body_text)

    if data.get("state") in STATE_TO_COUNTRY:
        data["country"] = STATE_TO_COUNTRY[data["state"]]

    # Tactical extraction
    min_c, max_c = extract_cadre_numbers(body_text)
    data["cadres_min"] = min_c
    data["cadres_max"] = max_c

    data["leader"] = extract_leaders(body_text)
    data["engagement_type_reasoned"] = detect_event_type(body_text)
    data["weapons"] = extract_weapons(body_text)
    data["ammunition"] = extract_ammunition(body_text)

    return data