from unittest.mock import patch, MagicMock, PropertyMock

import pytest
from PIL import Image

from app.ocr import (
    pdf_to_images,
    resize_image,
    pil_to_bgr_array,
    ocr_image,
    extract_text_from_pdf,
    extract_text,
)


class TestPdfToImages:
    @patch("app.ocr.convert_from_path")
    def test_delegates(self, mock_convert):
        mock_convert.return_value = [MagicMock(spec=Image.Image)]
        result = pdf_to_images("/fake.pdf", dpi=150)
        mock_convert.assert_called_once_with("/fake.pdf", dpi=150)
        assert len(result) == 1


class TestResizeImage:
    def test_no_resize_needed(self):
        img = MagicMock(spec=Image.Image)
        img.size = (400, 300)
        result = resize_image(img)
        assert result is img

    def test_resize_large(self):
        img = MagicMock(spec=Image.Image)
        img.size = (1600, 1200)
        result = resize_image(img)
        img.thumbnail.assert_called_once_with((800, 1000))
        assert result is img


class TestPilToBgrArray:
    def test_converts(self):
        img = Image.new("RGB", (2, 2), color=(255, 0, 0))
        arr = pil_to_bgr_array(img)
        assert arr.shape == (2, 2, 3)
        assert arr[0, 0].tolist() == [0, 0, 255]


class TestOcrImage:
    @patch("app.ocr.get_ocr")
    def test_returns_text(self, mock_get_ocr):
        mock_ocr = MagicMock()
        mock_result = MagicMock()
        mock_result.json = {"res": {"rec_texts": ["hello", "world"]}}
        mock_ocr.predict.return_value = [mock_result]
        mock_get_ocr.return_value = mock_ocr

        img = Image.new("RGB", (100, 50), color=(255, 255, 255))

        result = ocr_image(img)
        assert result == "hello\nworld"


class TestExtractText:
    @patch("app.ocr.extract_text_from_pdf")
    def test_pdf(self, mock_extract):
        mock_extract.return_value = "pdf text"
        result = extract_text(b"%PDF-data", "test.pdf")
        assert result == "pdf text"

    @patch("app.ocr.Image.open")
    @patch("app.ocr.ocr_image")
    def test_image(self, mock_ocr_image, mock_open):
        mock_ocr_image.return_value = "image text"
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
