from unittest.mock import patch, MagicMock

import pytest
from PIL import Image

from app.ocr import (
    pdf_to_images,
    ocr_image,
    ocr_image_detailed,
    ocr_pdf,
    ocr_pdf_from_bytes,
)


class TestPdfToImages:
    @patch("app.ocr.convert_from_path")
    def test_delegates(self, mock_convert):
        mock_convert.return_value = [MagicMock(spec=Image.Image)]
        result = pdf_to_images("/fake.pdf", dpi=300)
        mock_convert.assert_called_once_with("/fake.pdf", dpi=300)
        assert len(result) == 1


class TestOcrImage:
    @patch("app.ocr.pytesseract.image_to_string")
    def test_returns_text(self, mock_to_string):
        mock_to_string.return_value = "extracted text"
        img = MagicMock(spec=Image.Image)
        assert ocr_image(img) == "extracted text"
        mock_to_string.assert_called_once_with(img)


class TestOcrImageDetailed:
    @patch("app.ocr.pytesseract.image_to_data")
    def test_filters_empty_and_low_conf(self, mock_data):
        mock_data.return_value = {
            "text": ["hello", "", "world", "foo"],
            "conf": ["95", "-1", "80", "0"],
            "left": [0, 0, 0, 0],
            "top": [0, 0, 0, 0],
            "width": [0, 0, 0, 0],
            "height": [0, 0, 0, 0],
        }
        img = MagicMock(spec=Image.Image)
        results = ocr_image_detailed(img)
        assert len(results) == 2
        assert results[0]["text"] == "hello"
        assert results[0]["confidence"] == 95
        assert results[1]["text"] == "world"

    @patch("app.ocr.pytesseract.image_to_data")
    def test_empty_input(self, mock_data):
        mock_data.return_value = {
            "text": [],
            "conf": [],
            "left": [],
            "top": [],
            "width": [],
            "height": [],
        }
        img = MagicMock(spec=Image.Image)
        assert ocr_image_detailed(img) == []


class TestOcrPdf:
    @patch("app.ocr.pdf_to_images")
    @patch("app.ocr.ocr_image")
    def test_multi_page(self, mock_ocr_image, mock_pdf_to_images):
        mock_pdf_to_images.return_value = [MagicMock(), MagicMock()]
        mock_ocr_image.side_effect = ["page1 text", "page2 text"]
        page_texts, full = ocr_pdf("/fake.pdf")
        assert page_texts == ["page1 text", "page2 text"]
        assert full == "page1 text\n\npage2 text"


class TestOcrPdfFromBytes:
    @patch("app.ocr.ocr_pdf")
    @patch("app.ocr.tempfile.NamedTemporaryFile")
    def test_happy_path(self, mock_tempfile, mock_ocr_pdf):
        mock_file = MagicMock()
        mock_file.name = "/tmp/tmp123.pdf"
        mock_tempfile.__enter__.return_value = mock_file
        mock_ocr_pdf.return_value = (["hello"], "hello")

        page_texts, full = ocr_pdf_from_bytes(b"pdf data")
        assert page_texts == ["hello"]
        assert full == "hello"

    @patch("app.ocr.ocr_pdf")
    @patch("app.ocr.tempfile.NamedTemporaryFile")
    @patch("app.ocr.Path.unlink")
    def test_cleans_up_on_success(self, mock_unlink, mock_tempfile, mock_ocr_pdf):
        mock_file = MagicMock()
        mock_file.name = "/tmp/tmp123.pdf"
        mock_tempfile.__enter__.return_value = mock_file
        mock_ocr_pdf.return_value = (["t"], "t")

        ocr_pdf_from_bytes(b"data")
        mock_unlink.assert_called_once_with(missing_ok=True)

    @patch("app.ocr.ocr_pdf")
    @patch("app.ocr.tempfile.NamedTemporaryFile")
    @patch("app.ocr.Path.unlink")
    def test_cleans_up_on_error(self, mock_unlink, mock_tempfile, mock_ocr_pdf):
        mock_file = MagicMock()
        mock_file.name = "/tmp/tmp123.pdf"
        mock_tempfile.__enter__.return_value = mock_file
        mock_ocr_pdf.side_effect = RuntimeError("ocr fail")

        with pytest.raises(RuntimeError):
            ocr_pdf_from_bytes(b"data")
        mock_unlink.assert_called_once_with(missing_ok=True)
