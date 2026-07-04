import pdfplumber

from bot.utils.logger import logger

MIN_READABLE_CHARS = 50
TRUNCATION_SUFFIX = "\n\n[...metin kisaltildi...]"


class PdfService:
    def __init__(self, max_chars: int = 8000) -> None:
        self.max_chars = max_chars

    def extract_text(self, file_path: str) -> str:
        pages: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)

        text = "\n\n".join(pages).strip()
        logger.info("PDF extracted characters: %s", len(text))

        if len(text) < MIN_READABLE_CHARS:
            raise ValueError(
                "Bu PDF'te okunabilir metin bulamadim, taranmis bir "
                "belge olabilir."
            )

        if len(text) > self.max_chars:
            text = text[: self.max_chars] + TRUNCATION_SUFFIX

        return text
