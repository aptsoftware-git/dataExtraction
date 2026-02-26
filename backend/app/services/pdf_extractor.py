import os
import tempfile
from dotenv import load_dotenv

# ==========================================
# Environment Setup
# ==========================================

load_dotenv()

SAVE_DEBUG_MD = os.getenv("SAVE_DEBUG_MD", "false").lower() == "true"

# Force Camelot temp files to use project folder (fix Windows locking issue)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_DIR, "temp_camelot")

os.makedirs(TEMP_DIR, exist_ok=True)
tempfile.tempdir = TEMP_DIR

import pdfplumber
import camelot
from markdownify import markdownify as md
from app.utils.logger import log


# ==========================================
# Detect PDF Type
# ==========================================

def detect_pdf_type(pdf_path: str) -> str:
    """
    Detect if PDF is table-based or narrative.
    Uses Camelot detection first.
    """

    try:
        tables = camelot.read_pdf(pdf_path, pages="1", flavor="lattice")

        if tables and tables.n > 0:
            log("DETECT", "Table-based PDF detected (Camelot)")
            return "table"

    except Exception as e:
        log("DETECT", f"Camelot detection failed: {str(e)}")

    log("DETECT", "Narrative PDF detected")
    return "narrative"


# ==========================================
# TABLE PIPELINE
# ==========================================

def extract_table_rows_as_markdown(pdf_path: str) -> list:

    rows_markdown = []

    try:
        tables = camelot.read_pdf(pdf_path, pages="all", flavor="lattice")

        if tables.n == 0:
            raise Exception("No tables found by Camelot")

        for table in tables:
            df = table.df
            headers = df.iloc[0].tolist()

            for i in range(1, len(df)):
                row = df.iloc[i].tolist()
                row_dict = {}

                for col_idx in range(len(headers)):
                    header = str(headers[col_idx]).strip()
                    value = str(row[col_idx]).strip()

                    if value:
                        row_dict[header] = value

                row_md = "\n".join(
                    [f"**{k}**: {v}" for k, v in row_dict.items()]
                )

                if len(row_md.strip()) > 30:
                    rows_markdown.append(row_md)

        log("TABLE", f"Extracted {len(rows_markdown)} rows using Camelot")

    except Exception as e:

        log("TABLE", f"Camelot failed → fallback to pdfplumber: {str(e)}")

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()

                for table in tables:
                    headers = table[0]

                    for row in table[1:]:

                        row_dict = {}

                        for i in range(len(headers)):
                            header = str(headers[i]).strip()
                            value = str(row[i]).strip() if row[i] else ""

                            if value:
                                row_dict[header] = value

                        row_md = "\n".join(
                            [f"**{k}**: {v}" for k, v in row_dict.items()]
                        )

                        if len(row_md.strip()) > 30:
                            rows_markdown.append(row_md)

    # Save debug markdown only if enabled in .env
    if SAVE_DEBUG_MD:
        os.makedirs("debug_md", exist_ok=True)

        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        md_path = os.path.join("debug_md", f"{base_name}_table.md")

        with open(md_path, "w", encoding="utf-8") as f:
            for row in rows_markdown:
                f.write(row + "\n\n---\n\n")

        log("DEBUG", f"Table markdown saved → {md_path}")

    return rows_markdown


# ==========================================
# NARRATIVE PIPELINE
# ==========================================

def extract_narrative_markdown(pdf_path: str) -> str:

    html_content = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if text:
                html_content += f"<p>{text}</p>\n"

    if not html_content.strip():
        return ""

    markdown = md(html_content).strip()

    if SAVE_DEBUG_MD:
        os.makedirs("debug_md", exist_ok=True)

        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        md_path = os.path.join("debug_md", f"{base_name}_narrative.md")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        log("DEBUG", f"Narrative markdown saved → {md_path}")

    return markdown