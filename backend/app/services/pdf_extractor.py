import re
import pdfplumber
from app.utils.logger import log


# -----------------------------
# SPLIT NARRATIVE BLOCKS
# -----------------------------

def split_narrative_blocks(text):
    pattern = r'(?m)^\s*(\d{1,2})\.\s'

    matches = list(re.finditer(pattern, text))
    blocks = []

    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        blocks.append(block)

    log("PDF", f"Extracted {len(blocks)} narrative blocks")
    return blocks


# -----------------------------
# EXTRACT TABLE ROWS (FIXED)
# -----------------------------

def extract_table_rows(pdf_path):
    log("PDF", "Extracting structured table rows")

    rows = []
    current_row = None

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()

            if not tables:
                continue

            for table in tables:
                for row in table:
                    if not row:
                        continue

                    first_cell = str(row[0]).strip() if row[0] else ""

                    # Skip headers
                    if "Ser" in first_cell or "S/No" in first_cell:
                        continue

                    # Detect MAIN row only (1., 2., 3.)
                    if re.match(r'^\d+\.$', first_cell):

                        if current_row:
                            rows.append(current_row)

                        current_row = row.copy()

                    else:
                        # Merge sub-rows into current row
                        if current_row:
                            for i in range(len(row)):
                                if row[i]:
                                    if i < len(current_row) and current_row[i]:
                                        current_row[i] += " " + str(row[i])
                                    elif i < len(current_row):
                                        current_row[i] = row[i]

        if current_row:
            rows.append(current_row)

    log("PDF", f"Extracted {len(rows)} structured rows")
    return rows


# -----------------------------
# FULL TEXT EXTRACTION
# -----------------------------

def extract_text_from_pdf(pdf_path):
    log("PDF", "Extracting full text (narrative mode)")

    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text
