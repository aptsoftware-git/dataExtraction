from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil

from app.services.pdf_extractor import (
    detect_pdf_type,
    extract_narrative_markdown,
    extract_table_rows_as_markdown
)
from app.services.splitter import split_records
from app.services.local_llm_extractor import extract_multiple_blocks_parallel
from app.utils.logger import log

router = APIRouter()


@router.post("/upload")
async def upload(file: UploadFile = File(...)):

    try:
        os.makedirs("uploads", exist_ok=True)

        # Sanitize filename
        safe_filename = os.path.basename(file.filename)
        pdf_path = os.path.join("uploads", safe_filename)

        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        log("UPLOAD", safe_filename)

        # =====================================
        # Detect PDF Type
        # =====================================
        pdf_type = detect_pdf_type(pdf_path)

        # =====================================
        # TABLE PDF
        # =====================================
        if pdf_type == "table":

            blocks = extract_table_rows_as_markdown(pdf_path)

            if not blocks:
                raise HTTPException(
                    status_code=400,
                    detail="No table rows extracted"
                )

        # =====================================
        # NARRATIVE PDF
        # =====================================
        else:

            markdown_text = extract_narrative_markdown(pdf_path)

            if not markdown_text:
                raise HTTPException(
                    status_code=400,
                    detail="No readable text found"
                )

            blocks = split_records(markdown_text)

            if not blocks:
                blocks = [markdown_text]

        # =====================================
        # Filter Garbage Blocks (IMPORTANT)
        # =====================================
        blocks = [
            b for b in blocks
            if b and len(b.strip()) > 50
        ]

        if not blocks:
            raise HTTPException(
                status_code=400,
                detail="No valid intelligence records detected"
            )

        log("PROCESS", f"Sending {len(blocks)} blocks to LLM")

        results = extract_multiple_blocks_parallel(blocks)

        return JSONResponse({
            "status": "success",
            "records": len(results),
            "data": results
        })

    except HTTPException:
        raise

    except Exception as e:
        log("ERROR", str(e))
        raise HTTPException(
            status_code=500,
            detail="Processing failed"
        )