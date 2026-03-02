import os
from dotenv import load_dotenv
import pdfplumber
import camelot
from markdownify import markdownify as md
from app.utils.logger import log

# ==========================================
# Environment Setup
# ==========================================

load_dotenv()

SAVE_DEBUG_MD = os.getenv("SAVE_DEBUG_MD", "false").lower() == "true"


# ==========================================
# Detect PDF Type
# ==========================================

def detect_pdf_type(pdf_path: str) -> str:
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
# UNIVERSAL RAW HTML SAVER
# ==========================================

def save_raw_html(pdf_path: str):
    """
    Saves raw HTML version of extracted PDF text
    for BOTH table and narrative PDFs.
    """

    if not SAVE_DEBUG_MD:
        return

    os.makedirs("debug_output", exist_ok=True)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    html_path = os.path.join("debug_output", f"{base_name}_raw.html")

    html_content = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                html_content += f"<p>{text}</p>\n"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    log("DEBUG", f"Saved RAW HTML → {html_path}")


# ==========================================
# TABLE PIPELINE
# ==========================================

def extract_table_rows_as_markdown(pdf_path: str) -> list:

    # Always save raw HTML first
    save_raw_html(pdf_path)

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

    # Save markdown for table
    if SAVE_DEBUG_MD:
        os.makedirs("debug_output", exist_ok=True)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        md_path = os.path.join("debug_output", f"{base_name}_table.md")

        with open(md_path, "w", encoding="utf-8") as f:
            for row in rows_markdown:
                f.write(row + "\n\n---\n\n")

        log("DEBUG", f"Saved Table Markdown → {md_path}")

    return rows_markdown


# ==========================================
# NARRATIVE PIPELINE
# ==========================================

def extract_narrative_markdown(pdf_path: str) -> str:

    # Always save raw HTML first
    save_raw_html(pdf_path)

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
        os.makedirs("debug_output", exist_ok=True)

        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        md_path = os.path.join("debug_output", f"{base_name}_narrative.md")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        log("DEBUG", f"Saved Narrative Markdown → {md_path}")

    return markdown