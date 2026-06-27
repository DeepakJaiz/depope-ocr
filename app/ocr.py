import tempfile
from pathlib import Path

import numpy as np
from pdf2image import convert_from_path
from PIL import Image
from paddleocr import PaddleOCR

from app.logger import Timer, log

MAX_W = 800
MAX_H = 1000
PDF_RENDER_DPI = 150
N_CORES = 8


_ocr_instance: PaddleOCR | None = None


def get_ocr() -> PaddleOCR:
    global _ocr_instance
    if _ocr_instance is None:
        log.info("Loading PaddleOCR model (first request)...")
        with Timer("ocr.model_load"):
            _ocr_instance = PaddleOCR(
                text_detection_model_name="PP-OCRv6_tiny_det",
                text_recognition_model_name="PP-OCRv6_small_rec",
                device="cpu",
                cpu_threads=N_CORES,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                enable_mkldnn=True,
                engine="onnxruntime",
                precision="fp32",
            )
    return _ocr_instance


def reset_ocr():
    global _ocr_instance
    _ocr_instance = None


def resize_image(img: Image.Image) -> Image.Image:
    w, h = img.size
    if w > MAX_W or h > MAX_H:
        img.thumbnail((MAX_W, MAX_H))
    return img


def pil_to_bgr_array(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("RGB"))[:, :, ::-1]


def pdf_to_images(pdf_path: str, dpi: int = PDF_RENDER_DPI) -> list[Image.Image]:
    with Timer("pdf_to_images"):
        return convert_from_path(pdf_path, dpi=dpi)


def ocr_image(img: Image.Image, hint: str = "") -> str:
    ocr = get_ocr()
    img = resize_image(img)
    img_array = pil_to_bgr_array(img)
    tag = f"ocr({hint})" if hint else "ocr"
    with Timer(tag):
        result = ocr.predict(img_array)

    lines = []
    for res in result:
        texts = res.json.get("res", {}).get("rec_texts", [])
        lines.extend(texts)
    log.info("%s → %d lines", tag, len(lines))
    return "\n".join(lines)


def extract_text_from_pdf(pdf_path: str) -> str:
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
                img = Image.open(tmp_path)
                result = ocr_image(img, hint="image")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return result
