from flask import Blueprint, request, jsonify
import os
import re
from datetime import datetime

from app.services.pdf_extractor import (
    extract_text_from_pdf,
    split_narrative_blocks
)

from app.services.mapping_rules import apply_mapping
from app.services.excel_writer import write_excel
from app.utils.logger import log

upload_bp = Blueprint("upload", __name__)


def extract_date(text):
    if not text:
        return None

    match = re.search(r'\b\d{1,2}\s+[A-Za-z]{3}\s+\d{2}\b', text)
    if match:
        try:
            dt = datetime.strptime(match.group(0), "%d %b %y")
            return dt.strftime("%d-%b-%y")
        except:
            return match.group(0)

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

        full_text = extract_text_from_pdf(pdf_path)
        blocks = split_narrative_blocks(full_text)

        rows = []
        current_faction = None

        for idx, block in enumerate(blocks, start=1):

            input_text = re.sub(r'\s+', ' ', block).strip()

            if re.fullmatch(r'[A-Z]{3,6}', input_text):
                current_faction = input_text
                continue

            data = {
                "date": extract_date(input_text),
                "fmn": None,
                "aor_lower_fmn": None,
                "unit": None,
                "agency": None,
                "country": None,
                "state": None,
                "district": None,
                "gen_area": None,
                "gp": current_faction,
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

            data = apply_mapping(data, input_text)

            clean_text = re.sub(r'^\s*\d+\.\s*', '', input_text)
            heading_match = re.match(r'^([^\.]+)\.', clean_text)

            if heading_match:
                data["heading"] = heading_match.group(1).strip()
            else:
                data["heading"] = clean_text[:120]

            sentences = re.split(r'(?<=\.)\s+', clean_text)
            data["input_summary"] = " ".join(sentences[:3]).strip()

            rows.append(data)

        log("INFO", f"Rows built: {len(rows)}")

        final_excel = write_excel(rows, pdf_path)

        return jsonify({
            "status": "success",
            "message": f"Processed {len(rows)} records successfully",
            "excel": final_excel
        }), 200

    except Exception as e:
        log("ERROR", str(e))
        return jsonify({
            "status": "error",
            "message": "File processing failed"
        }), 500