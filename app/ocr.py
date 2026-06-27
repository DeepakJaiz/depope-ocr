import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from pdf2image import convert_from_path
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
        log.info("Loading OCR model (first request — one-time load)...")
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


def pdf_to_images(pdf_path: Path) -> list[Image.Image]:
    with Timer("ocr.pdf_to_images"):
        return convert_from_path(str(pdf_path), dpi=PDF_RENDER_DPI)


def extract_text_from_image(img: Image.Image, page_hint: str = "") -> str:
    ocr = get_ocr()
    img = resize_image(img)
    img_array = pil_to_bgr_array(img)
    tag = f"ocr.predict({page_hint})" if page_hint else "ocr.predict"
    with Timer(tag):
        result = ocr.predict(img_array)

    lines = []
    for res in result:
        texts = res.json.get("res", {}).get("rec_texts", [])
        lines.extend(texts)
    log.info("%s → %d text lines", tag, len(lines))
    return "\n".join(lines)


def extract_text_from_pdf(pdf_path: Path) -> str:
    images = pdf_to_images(pdf_path)
    all_text = []
    for i, img in enumerate(images):
        text = extract_text_from_image(img, page_hint=f"page_{i}")
        all_text.append(text)
    return "\n\n".join(all_text)


def extract_text(file_bytes: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    log.info("Processing file=%s size=%d bytes", filename, len(file_bytes))
    try:
        with Timer(f"ocr.total({filename})"):
            if suffix == ".pdf":
                result = extract_text_from_pdf(Path(tmp_path))
            else:
                img = Image.open(tmp_path)
                result = extract_text_from_image(img)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return result
