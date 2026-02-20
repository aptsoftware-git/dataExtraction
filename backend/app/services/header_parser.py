import re
from app.utils.logger import log

STATE_ABBR = {
    "UK": "Uttarakhand",
    "UP": "Uttar Pradesh",
    "MP": "Madhya Pradesh",
    "JK": "Jammu And Kashmir",
    "J&K": "Jammu And Kashmir",
    "WB": "West Bengal",
    "CG": "Chhattisgarh"
}

STATE_TO_COUNTRY = {
    "Uttarakhand": "India",
    "Uttar Pradesh": "India",
    "Madhya Pradesh": "India",
    "Jammu And Kashmir": "India",
    "West Bengal": "India",
    "Chhattisgarh": "India"
}


def parse_header(header: str) -> dict:
    data = {
        "date": None,
        "fmn": None,
        "aor_lower_fmn": None,
        "unit": None,
        "agency": None,
        "state": None,
        "district": None,
        "gen_area": None,
        "gp": None,
        "country": None
    }

    # Extract date first
    date_match = re.search(r"\b\d{1,2}[-\s][A-Za-z]{3}[-\s]\d{2}\b", header)
    if date_match:
        data["date"] = date_match.group()

        # Split header around date
        parts = header.split(date_match.group())

        if len(parts) > 1:
            after_date = parts[1].strip().split()

            # First token after date = Source (FMN)
            if len(after_date) > 0:
                data["fmn"] = after_date[0]

            # Second token after date = Faction (GP)
            if len(after_date) > 1:
                data["gp"] = after_date[1]

    log("HEADER", f"Parsed header → {data}")
    return data
