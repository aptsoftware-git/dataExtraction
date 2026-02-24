import re

# =====================================================
# COUNTRY / STATE
# =====================================================

STATE_TO_COUNTRY = {
    "Assam": "India",
    "Manipur": "India",
    "Nagaland": "India",
    "Arunachal Pradesh": "India",
    "West Bengal": "India"
}

KNOWN_DISTRICTS = [
    "Tinsukia","Namsai","Dimapur","Chumukedima",
    "Mon","Longleng","Tengnoupal","Pherzawl",
    "Noney","Changlang","KPI","CCpur",
    "Thoubal","Imphal","Langol"
]

# =====================================================
# HEADING + SUMMARY ENGINE
# =====================================================

def extract_heading_and_summary(text):

    # Remove numbering prefix (1. 2. 12. etc.)
    clean = re.sub(r'^\s*\d+\.\s*', '', text).strip()

    # Split into sentences
    sentences = re.split(r'(?<=\.)\s+', clean)

    if not sentences:
        return None, clean[:300]

    # Heading = first sentence without trailing dot
    heading = sentences[0].strip()
    if heading.endswith("."):
        heading = heading[:-1]

    # Summary = next 2–3 sentences
    summary_sentences = sentences[1:4]

    if summary_sentences:
        summary = " ".join(summary_sentences).strip()
    else:
        summary = clean

    # Limit size for Excel safety
    summary = summary[:800]

    return heading[:150], summary


# =====================================================
# SOURCE EXTRACTION
# =====================================================

def extract_source_fields(text):

    agency = None
    aor = None
    unit = None

    match = re.search(r'\(Source-\s*(.*?)\)', text)
    if not match:
        return agency, aor, unit

    parts = [p.strip() for p in match.group(1).split(",")]

    for p in parts:
        if "AOR" in p:
            aor = p.strip()
        elif "Unit" in p:
            unit = p.replace("Unit","").strip()
        else:
            agency = p

    return agency, aor, unit


# =====================================================
# FMN STRUCTURAL DETECTION
# =====================================================

def extract_fmn(text):

    if re.search(r'\bCOB\b', text):
        return "COB"
    if re.search(r'\bcamp\b', text, re.IGNORECASE):
        return "Camp"
    if re.search(r'\bpost\b', text, re.IGNORECASE):
        return "Post"
    if re.search(r'\bunit\b', text, re.IGNORECASE):
        return "Unit"

    return None


# =====================================================
# GP CONTEXTUAL EXTRACTION
# =====================================================

def extract_gp(text):

    patterns = [
        r'\b([A-Z]{3,6})\s+cadre',
        r'cadres?\s+of\s+([A-Z]{3,6})',
        r'\b([A-Z]{3,6})\s+COB',
        r'\b([A-Z]{3,6})\s+camp',
        r'\b([A-Z]{3,6})\s+is\s+plg'
    ]

    for p in patterns:
        match = re.search(p, text)
        if match:
            return match.group(1)

    return None


# =====================================================
# STATE & DISTRICT
# =====================================================

def extract_state(text):
    for state in STATE_TO_COUNTRY:
        if state.lower() in text.lower():
            return state
    return None

def extract_district(text):

    found = [d for d in KNOWN_DISTRICTS if d.lower() in text.lower()]

    if found:
        return " / ".join(sorted(set(found)))

    match = re.search(r'([A-Z][a-zA-Z]+)\s+(Dist|District)', text)
    if match:
        return match.group(1)

    return None


# =====================================================
# LEADER EXTRACTION
# =====================================================

def extract_leaders(text):

    leaders = []

    named = re.findall(r'named\s+([A-Z]{1,3}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
    leaders.extend(named)

    led_by = re.findall(r'led by\s+([A-Z]{1,3}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
    leaders.extend(led_by)

    rank_pattern = r'\bSS\s+(?:Lt|Maj|Capt|Col|Gen|Sgt(?:\s+Maj)?)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?'
    rank_matches = re.findall(rank_pattern, text)
    leaders.extend(rank_matches)

    seen = set()
    final = []
    for l in leaders:
        if l not in seen:
            final.append(l)
            seen.add(l)

    return ", ".join(final) if final else None


# =====================================================
# CADRE EXTRACTION
# =====================================================

def extract_cadre_numbers(text):

    match = re.search(r'gp\s+of\s+(\d+)\s*[/\-]\s*(\d+)\s*cadres', text, re.IGNORECASE)
    if match:
        return int(match.group(1)), int(match.group(2))

    match = re.search(r'approx\s+(\d+)\s*x', text, re.IGNORECASE)
    if match:
        n = int(match.group(1))
        return n, n

    match = re.search(r'(\d+)\s*x\s*cadres', text, re.IGNORECASE)
    if match:
        n = int(match.group(1))
        return n, n

    return None, None


# =====================================================
# EVENT CLASSIFICATION
# =====================================================

def detect_event_type(text):

    t = text.lower()

    if "standoff firing" in t:
        return "Standoff Firing"

    if "ablaze" in t or "burn" in t:
        return "Ablaze/ Conflict"

    if "infilt" in t:
        return "Infiltration"

    if "mov of cadres" in t or "movement of cadres" in t:
        return "Movement of Cadres"

    if "presence of cadres" in t:
        return "Presence of Cadres"

    if "mtg" in t or "meeting" in t:
        return "Meeting"

    if "plg" in t:
        return "Planning"

    if "firing" in t or "attack" in t:
        return "Firefight"

    return "IFC"


# =====================================================
# WEAPONS
# =====================================================

def extract_weapons(text):

    weapons = []

    if "rpg" in text.lower():
        weapons.append("RPG")

    if "gren" in text.lower():
        weapons.append("GRENADE")

    if "sa fire" in text.lower():
        weapons.append("SA")

    if "ied" in text.lower():
        weapons.append("IED")

    return ", ".join(sorted(set(weapons))) if weapons else None


def extract_ammunition(text):

    match = re.search(r'(\d+)\s*x\s*(?:rpg\s*)?(?:rounds?|rds)', text.lower())
    if match:
        return match.group(1)

    return None


# =====================================================
# MASTER APPLY
# =====================================================

def apply_mapping(data, body_text):

    # Heading + Summary
    heading, summary = extract_heading_and_summary(body_text)
    data["heading"] = heading
    data["input_summary"] = summary

    agency, aor, unit = extract_source_fields(body_text)

    if agency:
        data["agency"] = agency
    if aor:
        data["aor_lower_fmn"] = aor
    if unit:
        data["unit"] = unit

    data["fmn"] = extract_fmn(body_text)

    gp = extract_gp(body_text)
    if gp:
        data["gp"] = gp

    state = extract_state(body_text)
    if state:
        data["state"] = state
        data["country"] = STATE_TO_COUNTRY.get(state)

    data["district"] = extract_district(body_text)

    min_c, max_c = extract_cadre_numbers(body_text)
    data["cadres_min"] = min_c
    data["cadres_max"] = max_c

    data["leader"] = extract_leaders(body_text)
    data["engagement_type_reasoned"] = detect_event_type(body_text)
    data["weapons"] = extract_weapons(body_text)
    data["ammunition"] = extract_ammunition(body_text)

    return data