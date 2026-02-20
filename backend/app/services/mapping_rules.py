import re
from app.utils.logger import log


# =====================================================
# STATE & COUNTRY LOGIC
# =====================================================

STATE_ABBR = {
    "UK": "Uttarakhand",
    "UP": "Uttar Pradesh",
    "MP": "Madhya Pradesh",
    "JK": "Jammu And Kashmir",
    "WB": "West Bengal",
    "CG": "Chhattisgarh"
}

STATE_TO_COUNTRY = {
    "Uttarakhand": "India",
    "Uttar Pradesh": "India",
    "Madhya Pradesh": "India",
    "Jammu And Kashmir": "India",
    "West Bengal": "India",
    "Chhattisgarh": "India",
    "Manipur": "India",
    "Assam": "India",
    "Nagaland": "India",
    "Arunachal Pradesh": "India"
}


def normalize_state(state):
    if not state:
        return None

    s = state.strip().upper()

    if s in STATE_ABBR:
        return STATE_ABBR[s]

    return state.title()


def extract_state(text):
    if not text:
        return None

    for state in STATE_TO_COUNTRY.keys():
        if state.lower() in text.lower():
            return state

    return None


# =====================================================
# CADRE EXTRACTION
# =====================================================

def extract_cadre_numbers(text):
    if not text:
        return None, None

    matches = re.findall(
        r'(\d+)\s+(?:cadres?|militants?|terrorists?)',
        text,
        re.IGNORECASE
    )

    numbers = [int(m) for m in matches]

    if not numbers:
        return None, None

    return min(numbers), max(numbers)


# =====================================================
# EVENT TYPE DETECTION (PRIORITY BASED)
# =====================================================

def detect_event_type(text):
    if not text:
        return None

    t = text.lower()

    # 1️⃣ DEFLECTION
    if any(k in t for k in [
        "desert",
        "surrender",
        "joined rival",
        "defection"
    ]):
        return "Defection"

    # 2️⃣ FIREFIGHT / COMBAT
    if any(k in t for k in [
        "firefight",
        "firing",
        "exchange of fire",
        "gun battle",
        "ambush",
        "attack",
        "explosion",
        "ied blast",
        "grenade",
        "rpg",
        "rocket",
        "detonated"
    ]):
        return "Firefight"

    # 3️⃣ IFC
    if any(k in t for k in [
        "extortion",
        "movement",
        "meeting",
        "warning",
        "visit",
        "sharing",
        "instruction",
        "recruitment",
        "targeting",
        "conversation",
        "mobile call",
        "planning"
    ]):
        return "IFC"

    return None


# =====================================================
# LEADER EXTRACTION
# =====================================================

def extract_leaders(text):
    if not text:
        return None

    patterns = [
        r'named\s+([A-Za-z]+\s?[A-Za-z]*)',
        r'\b(?:Maj|Lt|Col|Gen|SS|Dy|Ato)\s+[A-Za-z]+'
    ]

    leaders = set()

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            leaders.add(m.strip())

    return ", ".join(leaders) if leaders else None


# =====================================================
# WEAPON EXTRACTION
# =====================================================

def extract_weapons(text):
    if not text:
        return None

    weapon_keywords = [
        "ak-47",
        "ak 47",
        "rifle",
        "pistol",
        "grenade",
        "ied",
        "rpg",
        "rocket",
        "lmg",
        "lmgs",
        "insas"
    ]

    found = []

    for weapon in weapon_keywords:
        if weapon.lower() in text.lower():
            found.append(weapon.upper())

    return ", ".join(set(found)) if found else None


# =====================================================
# AMMUNITION EXTRACTION
# =====================================================

def extract_ammunition(text):
    if not text:
        return None

    match = re.search(
        r'(\d+)\s*(?:rounds?|ammo|ammunition)',
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return None


# =====================================================
# DISTRICT EXTRACTION
# =====================================================

def extract_district(text):
    if not text:
        return None

    match = re.search(
        r'([A-Za-z]+)\s+(?:Dist|District)',
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return None


# =====================================================
# AOR EXTRACTION
# =====================================================

def extract_aor(text):
    if not text:
        return None

    match = re.search(
        r'AOR\s*([A-Za-z0-9\s]+)',
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return None


# =====================================================
# UNIT EXTRACTION
# =====================================================

def extract_unit(text):
    if not text:
        return None

    match = re.search(
        r'Unit\s*([A-Za-z0-9\s]+)',
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return None


# =====================================================
# APPLY MAPPING
# =====================================================

def apply_mapping(data: dict, body_text: str) -> dict:

    body_text = body_text or ""

    # Cadres
    min_c, max_c = extract_cadre_numbers(body_text)
    data["cadres_min"] = min_c
    data["cadres_max"] = max_c

    # Event Type
    data["engagement_type_reasoned"] = detect_event_type(body_text)

    # Leader
    data["leader"] = extract_leaders(body_text)

    # Weapons
    data["weapons"] = extract_weapons(body_text)

    # Ammunition
    data["ammunition"] = extract_ammunition(body_text)

    # District
    district = extract_district(body_text)
    if district:
        data["district"] = district

    # State
    state = extract_state(body_text)
    if state:
        data["state"] = state

    data["state"] = normalize_state(data.get("state"))

    # Country
    if not data.get("country") and data.get("state") in STATE_TO_COUNTRY:
        data["country"] = STATE_TO_COUNTRY[data["state"]]

    # AOR
    aor = extract_aor(body_text)
    if aor:
        data["aor"] = aor

    # Unit
    unit = extract_unit(body_text)
    if unit:
        data["unit"] = unit

    return data
