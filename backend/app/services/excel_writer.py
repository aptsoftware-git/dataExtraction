import os
import pandas as pd
from datetime import datetime
from app.schemas.intel_schema import EXCEL_COLUMNS
from app.utils.logger import log


def write_excel(rows, pdf_path):
    log("EXCEL", "Writing file")

    df = pd.DataFrame(rows)

    df = df.rename(columns={
        "date": "Date",
        "fmn": "FMN",
        "aor_lower_fmn": "AOR (LOWER FMN)",
        "unit": "Unit",
        "agency": "AGENCY",
        "country": "COUNTRY",
        "state": "STATE",
        "district": "DIST",
        "gen_area": "GEN A",
        "gp": "GP",
        "heading": "Heading",
        "input_summary": "Input",
        "coordinates": "Coordinates",
        "engagement_type_reasoned": "Defection To/ Firefight/ IFC With",
        "cadres_min": "No of Cadres (Min)",
        "cadres_max": "No of Cadres (Max)",
        "leader": "Ldr",
        "weapons": "Wpns",
        "ammunition": "Amn",
    })

    df = df.reindex(columns=EXCEL_COLUMNS)

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_path = f"output/{base_name}_{timestamp}.xlsx"

    df.to_excel(final_path, index=False)

    log("EXCEL", f"File saved → {final_path}")
    return final_path