from flask import Blueprint, request, jsonify
import os
import re

from app.services.pdf_extractor import (
    extract_table_rows,
    extract_text_from_pdf,
    split_narrative_blocks
)

from app.services.mapping_rules import apply_mapping
from app.services.local_llm_extractor import extract_semantic_fields
from app.services.excel_writer import write_excel
from app.utils.logger import log

upload_bp = Blueprint("upload", __name__)


# ---------------- UNIVERSAL DATE EXTRACTION ----------------
def extract_date(text):
    if not text:
        return None

    patterns = [
        r'\b\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4}\b',
        r'\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
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

        # ---------------- MODE DETECTION ----------------
        rows_data = extract_table_rows(pdf_path)

        if rows_data and len(rows_data[0]) >= 4:
            mode = "TABLE"
            log("MODE", "Detected TABLE structured document")
            source_rows = rows_data
        else:
            mode = "NARRATIVE"
            log("MODE", "Detected NARRATIVE structured document")
            full_text = extract_text_from_pdf(pdf_path)
            source_rows = split_narrative_blocks(full_text)

        rows = []
        failed_records = 0
        current_faction = None

        def safe_cell(value):
            if value is None:
                return ""
            return str(value).replace("\n", " ").strip()

        # ---------------- PROCESS RECORDS ----------------
        for idx, row in enumerate(source_rows, start=1):
            try:

                # ================= TABLE MODE =================
                if mode == "TABLE":
                    input_text = safe_cell(row[8]) if len(row) > 8 else ""
                    agency = safe_cell(row[2]) if len(row) > 2 else None
                    gp = safe_cell(row[3]) if len(row) > 3 else None
                    date = extract_date(input_text)
                    aor = None
                    unit = None

                # ================= NARRATIVE MODE =================
                else:
                    input_text = re.sub(r'\s+', ' ', row).strip()

                    # Detect faction header
                    if re.fullmatch(r'[A-Z]{3,6}', input_text):
                        current_faction = input_text
                        continue

                    gp = current_faction
                    date = extract_date(input_text)

                    source_match = re.search(r'\(Source-\s*(.*?)\)', input_text)

                    agency = None
                    aor = None
                    unit = None

                    if source_match:
                        source_text = source_match.group(1)
                        parts = [p.strip() for p in source_text.split(",")]

                        if len(parts) >= 1:
                            agency = parts[0]

                        for part in parts:
                            if "AOR" in part:
                                aor = part.replace("AOR", "").strip()
                            if "Unit" in part:
                                unit = part.replace("Unit", "").strip()

                # ---------------- BASE DATA ----------------
                data = {
                    "date": date,
                    "gp": gp if gp else None,
                    "state": None,
                    "district": None,
                    "country": None,
                    "gen_area": None,
                    "heading": None,
                    "input_summary": None,
                    "coordinates": None
                }

                # ---------------- DETERMINISTIC EXTRACTION ----------------
                data = apply_mapping(data, input_text)

                # ---------------- HEADING EXTRACTION ----------------
                # Remove numbering like "1. "
                clean_text = re.sub(r'^\s*\d+\.\s*', '', input_text)

                heading_match = re.match(r'^([^\.]+)\.', clean_text)

                if heading_match:
                    data["heading"] = heading_match.group(1).strip()

                # ---------------- LLM EXTRACTION ----------------
                try:
                    llm_data = extract_semantic_fields(input_text)
                except Exception as e:
                    log("LLM", f"LLM failed → {e}")
                    llm_data = {}

                # ---------------- CLEAN BODY FOR SUMMARY ----------------
                clean_body = re.sub(r'^\s*\d+\.\s*', '', input_text)
                clean_body = re.sub(r'^[^\.]+\.\s*', '', clean_body)

                summary = llm_data.get("input_summary")

                if summary and len(summary.strip()) > 20:
                    data["input_summary"] = summary.strip()
                else:
                    # fallback summary = first 3 sentences AFTER heading
                    sentences = re.split(r'(?<=\.)\s+', clean_body)
                    data["input_summary"] = " ".join(sentences[:3]).strip()

                # Final safety fallback for heading
                if not data.get("heading") and clean_body:
                    data["heading"] = clean_body.split(".")[0][:120].strip()

                # ---------------- FINAL APPEND ----------------
                rows.append({
                    "Date": data.get("date"),
                    "FMN": None,  # Always empty
                    "AOR (LOWER FMN)": aor,
                    "Unit": unit,
                    "AGENCY": agency,
                    "COUNTRY": data.get("country"),
                    "STATE": data.get("state"),
                    "DIST": data.get("district"),
                    "GEN A": data.get("gen_area"),
                    "GP": data.get("gp"),
                    "Heading": data.get("heading"),
                    "Input": data.get("input_summary"),
                    "Coordinates": data.get("coordinates"),
                    "Defection To/ Firefight/ IFC With": data.get("engagement_type_reasoned"),
                    "No of Cadres (Min)": data.get("cadres_min"),
                    "No of Cadres (Max)": data.get("cadres_max"),
                    "Ldr": data.get("leader"),
                    "Wpns": data.get("weapons"),
                    "Amn": data.get("ammunition")
                })

            except Exception as e:
                failed_records += 1
                log("ERROR", f"Row {idx} failed: {e}")

        log("VALIDATION", f"Records detected: {len(source_rows)}")
        log("VALIDATION", f"Rows processed: {len(rows)}")

        final_excel = write_excel(rows, pdf_path)

        log("DONE", f"Pipeline complete | Success: {len(rows)} | Failed: {failed_records}")

        return jsonify({
            "status": "success",
            "message": f"Processed {len(rows)} records successfully",
            "excel": final_excel
        }), 200

    except Exception as e:
        log("ERROR", f"Upload failed: {e}")
        return jsonify({
            "status": "error",
            "message": "File processing failed",
            "details": str(e)
        }), 500
