from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
import re
from datetime import datetime
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv

from app.services.pdf_extractor import (
    extract_table_rows,
    extract_text_from_pdf,
    split_narrative_blocks
)

from app.services.mapping_rules import apply_mapping
from app.services.local_llm_extractor import extract_semantic_fields, extract_multiple_blocks_parallel, LLM_SKIP_MAPPING
from app.services.excel_writer import write_excel
from app.utils.logger import log

# Load environment variables
load_dotenv()
EXTRACTION_MODE = os.getenv("EXTRACTION_MODE", "RULE-BASED")

router = APIRouter()


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


@router.post("/upload")
async def upload(file: UploadFile = File(...)):

    try:

        os.makedirs("uploads", exist_ok=True)
        os.makedirs("output", exist_ok=True)

        pdf_path = f"uploads/{file.filename}"
        
        # Save uploaded file
        with open(pdf_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        log("UPLOAD", file.filename)
        log("CONFIG", f"Extraction mode: {EXTRACTION_MODE}")

        rows = []

        table_rows = extract_table_rows(pdf_path)

        # =====================================================
        # TABLE MODE
        # =====================================================

        if table_rows and len(table_rows) > 1:

            log("MODE", "TABLE")
            log("INFO", "Using rule-based extraction (TABLE MODE doesn't use LLM)")

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

            log("MODE", f"NARRATIVE ({EXTRACTION_MODE})")

            full_text = extract_text_from_pdf(pdf_path)
            blocks = split_narrative_blocks(full_text)
            
            # Clean all blocks first
            clean_blocks = [re.sub(r'\s+', ' ', block).strip() for block in blocks]
            
            # LLM-BASED extraction with parallel processing
            if EXTRACTION_MODE == "LLM-BASED":
                log("EXTRACTION", f"Using parallel LLM-based extraction for {len(clean_blocks)} blocks")
                
                # Process all blocks in parallel (uses LLM_MAX_WORKERS from .env)
                llm_results = extract_multiple_blocks_parallel(clean_blocks)
                
                # Create data structures with LLM results
                for idx, clean_text in enumerate(clean_blocks):
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
                    
                    # Update with LLM extracted fields
                    llm_data = llm_results[idx]
                    for key, value in llm_data.items():
                        if key in data and value:
                            data[key] = value
                    
                    # Apply mapping rules only if LLM_SKIP_MAPPING is false
                    if not LLM_SKIP_MAPPING:
                        data = apply_mapping(data, clean_text)
                    
                    rows.append(data)
            
            # RULE-BASED extraction (sequential - fast enough)
            else:
                log("EXTRACTION", f"Using rule-based extraction for {len(clean_blocks)} blocks")
                
                for clean_text in clean_blocks:
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

        # Store extracted data (no automatic Excel generation)
        response_data = {
            "status": "success",
            "records": len(rows),
            "data": rows
        }
        
        return JSONResponse(content=response_data)

    except Exception as e:
        log("ERROR", str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Processing failed"
            }
        )


# =====================================================
# EXPORT ENDPOINT
# =====================================================

class ExportRequest(BaseModel):
    data: List[dict]
    filename: str = "intelligence_data"


@router.post("/export")
async def export_to_excel(request: ExportRequest):
    """
    Export selected or all records to Excel file
    """
    try:
        if not request.data or len(request.data) == 0:
            raise HTTPException(
                status_code=400,
                detail={"status": "error", "message": "No data to export"}
            )
        
        log("EXPORT", f"Exporting {len(request.data)} records")
        
        # Generate temporary Excel file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filename = f"{request.filename}_{timestamp}.xlsx"
        temp_path = f"output/{temp_filename}"
        
        # Use write_excel to generate the file
        excel_path = write_excel(request.data, temp_path)
        
        # Return file for download
        return FileResponse(
            path=excel_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=temp_filename,
            headers={"Content-Disposition": f"attachment; filename={temp_filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log("EXPORT_ERROR", str(e))
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Export failed: {str(e)}"}
        )