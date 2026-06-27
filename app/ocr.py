import tempfile
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from PIL import Image


def pdf_to_images(pdf_path: str, dpi: int = 300) -> list[Image.Image]:
    return convert_from_path(pdf_path, dpi=dpi)


def ocr_image(image: Image.Image) -> str:
    return pytesseract.image_to_string(image)


def ocr_image_detailed(image: Image.Image) -> list[dict]:
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    results = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        if text and int(data["conf"][i]) > 0:
            results.append({
                "text": text,
                "confidence": int(data["conf"][i]),
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
            })
    return results


def ocr_pdf(pdf_path: str, dpi: int = 300) -> tuple[list[str], str]:
    images = pdf_to_images(pdf_path, dpi=dpi)
    page_texts = []
    for img in images:
        text = ocr_image(img)
        page_texts.append(text)
    return page_texts, "\n\n".join(page_texts)


def ocr_pdf_from_bytes(pdf_bytes: bytes, dpi: int = 300) -> tuple[list[str], str]:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name
    try:
        return ocr_pdf(tmp_path, dpi=dpi)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
