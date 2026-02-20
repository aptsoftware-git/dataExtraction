import os
import pandas as pd
from datetime import datetime
from app.schemas.intel_schema import EXCEL_COLUMNS
from app.utils.logger import log


def write_excel(rows, pdf_path):
    log("EXCEL", "Writing file")

    df = pd.DataFrame(rows, columns=EXCEL_COLUMNS)

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    final_path = f"output/{base_name}_{timestamp}.xlsx"

    df.to_excel(final_path, index=False)

    log("EXCEL", f"File saved → {final_path}")
    return final_path
