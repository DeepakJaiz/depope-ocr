from unittest.mock import patch, MagicMock

import pytest
from PIL import Image

from app.ocr import (
    pdf_to_images,
    ocr_image,
    extract_text_from_pdf,
    extract_text_from_image,
    extract_text,
)


class TestPdfToImages:
    @patch("app.ocr.convert_from_path")
    def test_delegates(self, mock_convert):
        mock_convert.return_value = [MagicMock(spec=Image.Image)]
        result = pdf_to_images("/fake.pdf", dpi=150)
        mock_convert.assert_called_once_with("/fake.pdf", dpi=150)
        assert len(result) == 1


class TestOcrImage:
    @patch("app.ocr.pytesseract.image_to_string")
    def test_returns_text(self, mock_to_string):
        mock_to_string.return_value = "extracted text"
        img = MagicMock(spec=Image.Image)
        img.size = (400, 300)
        assert ocr_image(img) == "extracted text"


class TestExtractText:
    @patch("app.ocr.extract_text_from_pdf")
    def test_pdf(self, mock_extract):
        mock_extract.return_value = "pdf text"
        result = extract_text(b"%PDF-data", "test.pdf")
        assert result == "pdf text"

    @patch("app.ocr.extract_text_from_image")
    def test_image(self, mock_extract):
        mock_extract.return_value = "image text"
        result = extract_text(b"PNG-data", "test.png")
        assert result == "image text"

    @patch("app.ocr.extract_text_from_pdf")
    @patch("app.ocr.tempfile.NamedTemporaryFile")
    @patch("app.ocr.Path.unlink")
    def test_cleanup(self, mock_unlink, mock_tempfile, mock_extract):
        mock_file = MagicMock()
        mock_file.name = "/tmp/tmp123.pdf"
        mock_tempfile.__enter__.return_value = mock_file
        mock_extract.return_value = "text"

        extract_text(b"data", "test.pdf")
        mock_unlink.assert_called_once_with(missing_ok=True)
