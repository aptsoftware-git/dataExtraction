import re
from app.utils.logger import log


ROW_PATTERN = re.compile(
    r"(?:^|\n)\s*(\d{1,2})\.\s",
    re.MULTILINE
)


def split_records(text: str) -> list[str]:
    """
    Split Markdown into intelligence records.
    """

    log("SPLIT", "Splitting markdown")

    clean = re.sub(r"\n{2,}", "\n", text)

    matches = list(ROW_PATTERN.finditer(clean))

    if len(matches) <= 1:
        log("SPLIT", "Single record detected")
        return [clean.strip()]

    records = []

    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(clean)

        record = clean[start:end].strip()

        if len(record) > 50:
            records.append(record)

    log("SPLIT", f"Detected {len(records)} records")

    return records