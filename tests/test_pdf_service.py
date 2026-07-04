import unittest
from unittest.mock import patch

from bot.services.pdf_service import PdfService


class FakePage:
    def __init__(self, text: str | None) -> None:
        self._text = text

    def extract_text(self) -> str | None:
        return self._text


class FakePdf:
    def __init__(self, pages: list[FakePage]) -> None:
        self.pages = pages

    def __enter__(self) -> "FakePdf":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class PdfServiceTests(unittest.TestCase):
    def test_extracts_and_joins_text_from_all_pages(self) -> None:
        fake_pdf = FakePdf(
            [
                FakePage("Page one content " * 5),
                FakePage("Page two content " * 5),
            ]
        )
        with patch(
            "bot.services.pdf_service.pdfplumber.open",
            return_value=fake_pdf,
        ):
            service = PdfService()
            text = service.extract_text("fake.pdf")

        self.assertIn("Page one content", text)
        self.assertIn("Page two content", text)
        self.assertIn("\n\n", text)

    def test_raises_value_error_for_scanned_pdf_with_no_text(self) -> None:
        fake_pdf = FakePdf([FakePage(None), FakePage("")])
        with patch(
            "bot.services.pdf_service.pdfplumber.open",
            return_value=fake_pdf,
        ):
            service = PdfService()
            with self.assertRaises(ValueError):
                service.extract_text("scanned.pdf")

    def test_truncates_text_longer_than_max_chars(self) -> None:
        fake_pdf = FakePdf([FakePage("a" * 100)])
        with patch(
            "bot.services.pdf_service.pdfplumber.open",
            return_value=fake_pdf,
        ):
            service = PdfService(max_chars=20)
            text = service.extract_text("long.pdf")

        self.assertTrue(text.startswith("a" * 20))
        self.assertIn("[...metin kisaltildi...]", text)


if __name__ == "__main__":
    unittest.main()
