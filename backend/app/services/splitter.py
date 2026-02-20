import re
from app.utils.logger import log


ROW_PATTERN = re.compile(
    r"(?:^|\n)\s*(\d{1,2})\.\s",  # 1. 2. 3. ...
    re.MULTILINE
)


def split_records(text: str) -> list[str]:
    """
    Splits Army intelligence table PDFs into records
    using S/No row anchors (1., 2., 3., ...)
    """

    log("SPLIT", "Starting record splitting")

    # Clean text slightly
    clean = re.sub(r"[ \t]+", " ", text)
    clean = re.sub(r"\n{2,}", "\n", clean)

    matches = list(ROW_PATTERN.finditer(clean))

    if len(matches) <= 1:
        log("SPLIT", "Single record detected")
        return [clean.strip()]

    records = []

    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(clean)

        record = clean[start:end].strip()

        # ignore junk
        if len(record) > 80:
            records.append(record)

    log("SPLIT", f"Detected {len(records)} records")
    return records


def split_header_and_body(record: str):
    """
    Splits a single intelligence record into:
    - header: first logical line (table row)
    - body: remaining narrative inputs
    """
    lines = [l.strip() for l in record.split("\n") if l.strip()]
    header = lines[0]
    body = "\n".join(lines[1:]) if len(lines) > 1 else ""
    return header, body

