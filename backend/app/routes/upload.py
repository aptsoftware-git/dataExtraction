from flask import Blueprint, request, jsonify
import os
import re
from datetime import datetime

from app.services.pdf_extractor import (
    extract_table_rows,
    extract_text_from_pdf,
    split_narrative_blocks
)

from app.services.mapping_rules import apply_mapping
from app.services.excel_writer import write_excel
from app.utils.logger import log

upload_bp = Blueprint("upload", __name__)


# =====================================================
# UNIVERSAL DATE EXTRACTION
# =====================================================

def extract_date_anywhere(text):

    if not text:
        return None

    patterns = [
        r'\b\d{1,2}-[A-Za-z]{3}-\d{2}\b',
        r'\b\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4}\b'
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            try:
                dt = datetime.strptime(m.group(0), "%d-%b-%y")
                return dt.strftime("%d-%b-%y")
            except:
                return m.group(0)

    return None


@upload_bp.route("/upload", methods=["POST"])
def upload():

    try:

        file = request.files["file"]

        os.makedirs("uploads", exist_ok=True)
        os.makedirs("output", exist_ok=True)

        pdf_path = f"uploads/{file.filename}"
        file.save(pdf_path)

        log("UPLOAD", file.filename)

        rows = []

        table_rows = extract_table_rows(pdf_path)

        # =====================================================
        # TABLE MODE
        # =====================================================

        if table_rows and len(table_rows) > 1:

            log("MODE", "TABLE")

            header = [h.strip().lower() if h else "" for h in table_rows[0]]

            for row in table_rows[1:]:

                row_text = " ".join([str(c) for c in row if c])

                data = {
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
                    "input_summary": row_text,
                    "coordinates": None,
                    "engagement_type_reasoned": None,
                    "cadres_min": None,
                    "cadres_max": None,
                    "leader": None,
                    "weapons": None,
                    "ammunition": None
                }

                # STRUCTURED COLUMN MAPPING
                for idx, col_name in enumerate(header):

                    if idx >= len(row):
                        continue

                    cell = row[idx]
                    if not cell:
                        continue

                    cell_str = str(cell)

                    if "date" in col_name:
                        data["date"] = cell_str

                    if "source" in col_name:
                        data["agency"] = cell_str

                    if "faction" in col_name:
                        data["gp"] = cell_str

                    if "input" in col_name:
                        data["input_summary"] = cell_str

                # Fallback date from full row
                if not data["date"]:
                    data["date"] = extract_date_anywhere(row_text)

                # Heading extraction
                heading_match = re.match(r'^([^\.]+)\.', row_text)
                if heading_match:
                    data["heading"] = heading_match.group(1).strip()
                else:
                    data["heading"] = row_text[:100]

                # Semantic enrichment
                data = apply_mapping(data, row_text)

                rows.append(data)

        # =====================================================
        # NARRATIVE MODE
        # =====================================================

        else:

            log("MODE", "NARRATIVE")

            full_text = extract_text_from_pdf(pdf_path)
            blocks = split_narrative_blocks(full_text)

            for block in blocks:

                clean_text = re.sub(r'\s+', ' ', block).strip()

                data = {
                    "date": extract_date_anywhere(clean_text),
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
                    "input_summary": clean_text,
                    "coordinates": None,
                    "engagement_type_reasoned": None,
                    "cadres_min": None,
                    "cadres_max": None,
                    "leader": None,
                    "weapons": None,
                    "ammunition": None
                }

                heading_match = re.match(r'^([^\.]+)\.', clean_text)
                if heading_match:
                    data["heading"] = heading_match.group(1).strip()
                else:
                    data["heading"] = clean_text[:100]

                data = apply_mapping(data, clean_text)

                rows.append(data)

        final_excel = write_excel(rows, pdf_path)

        return jsonify({
            "status": "success",
            "records": len(rows),
            "excel": final_excel
        }), 200

    except Exception as e:
        log("ERROR", str(e))
        return jsonify({
            "status": "error",
            "message": "Processing failed"
        }), 500