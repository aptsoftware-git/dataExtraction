from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
from datetime import datetime
from typing import List
from pydantic import BaseModel

from app.services.pdf_extractor import pdf_to_markdown
from app.services.splitter import split_records
from app.services.local_llm_extractor import extract_multiple_blocks_parallel
from app.services.excel_writer import write_excel
from app.utils.logger import log

router = APIRouter()


@router.post("/upload")
async def upload(file: UploadFile = File(...)):

    try:
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("output", exist_ok=True)

        pdf_path = f"uploads/{file.filename}"

        with open(pdf_path, "wb") as buffer:
            buffer.write(await file.read())

        log("UPLOAD", file.filename)

        # PDF → Markdown
        markdown_text = pdf_to_markdown(pdf_path)

        if not markdown_text:
            raise HTTPException(status_code=400, detail="No readable text found")

        # Split records
        blocks = split_records(markdown_text)

        if not blocks:
            blocks = [markdown_text]

        log("PROCESS", f"Sending {len(blocks)} blocks to LLM")

        results = extract_multiple_blocks_parallel(blocks)

        return JSONResponse({
            "status": "success",
            "records": len(results),
            "data": results
        })

    except Exception as e:
        log("ERROR", str(e))
        raise HTTPException(status_code=500, detail="Processing failed")