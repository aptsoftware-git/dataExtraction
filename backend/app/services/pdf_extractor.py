import pdfplumber
from markdownify import markdownify as md
from app.utils.logger import log


def pdf_to_markdown(pdf_path: str) -> str:
    """
    Converts PDF → HTML → Markdown
    """

    log("PDF", "Converting PDF to HTML")

    html_content = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                html_content += f"<p>{text}</p>\n"

    if not html_content.strip():
        log("PDF", "No readable text found")
        return ""

    log("PDF", "Converting HTML to Markdown")

    markdown = md(html_content)

    return markdown.strip()