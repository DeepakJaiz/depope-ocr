import tempfile
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from PIL import Image

from app.logger import Timer, log

MAX_W = 800
MAX_H = 1000
PDF_RENDER_DPI = 150


def pdf_to_images(pdf_path: str, dpi: int = PDF_RENDER_DPI) -> list[Image.Image]:
    return convert_from_path(pdf_path, dpi=dpi)


def resize_image(img: Image.Image) -> Image.Image:
    w, h = img.size
    if w > MAX_W or h > MAX_H:
        img.thumbnail((MAX_W, MAX_H))
    return img


def ocr_image(img: Image.Image, hint: str = "") -> str:
    img = resize_image(img)
    tag = f"ocr({hint})" if hint else "ocr"
    with Timer(tag):
        text = pytesseract.image_to_string(img)
    log.info("%s → %d chars", tag, len(text))
    return text


def extract_text_from_pdf(pdf_path: str) -> str:
    with Timer("pdf_to_images"):
        images = pdf_to_images(pdf_path)
    all_text = []
    for i, img in enumerate(images):
        text = ocr_image(img, hint=f"page_{i}")
        all_text.append(text)
    return "\n\n".join(all_text)


def extract_text_from_image(img_path: str) -> str:
    img = Image.open(img_path)
    return ocr_image(img, hint="image")


def extract_text(file_bytes: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    log.info("Processing file=%s size=%d bytes", filename, len(file_bytes))
    try:
        with Timer(f"extract_text({filename})"):
            if suffix == ".pdf":
                result = extract_text_from_pdf(tmp_path)
            else:
                result = extract_text_from_image(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return result
