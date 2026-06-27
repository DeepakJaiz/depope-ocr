from fastapi import FastAPI, File, UploadFile

from app.logger import log
from app.models import ExtractionResponse, HealthResponse, ContainerInfo
from app.ocr import extract_text
from app.llm_service import extract_invoice_fields

app = FastAPI(
    title="Depope OCR",
    description="OCR extraction service for depot invoices — upload PDF/images, get structured depot/container data.",
    version="2.0.0",
)

SUPPORTED_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/tiff",
    "image/bmp",
}

MAX_FILE_SIZE = 50 * 1024 * 1024


def _normalise_containers(raw: list | dict | None) -> list[dict] | None:
    if raw is None:
        return None
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        keys = [k for k in raw if k != "type_size"]
        vals = [raw[k] for k in keys if raw[k]]
        if vals:
            return [{"number": v, "type_size": raw.get("type_size")} for v in vals]
    return None


@app.get("/health", response_model=HealthResponse)
async def health():
    ocr_loaded = True
    try:
        from app.ocr import get_ocr
        get_ocr()
    except Exception as e:
        log.error("OCR model load failed: %s", e)
        ocr_loaded = False

    return HealthResponse(status="ok", ocr_loaded=ocr_loaded)


@app.post("/api/v1/extract", response_model=ExtractionResponse)
async def extract(file: UploadFile = File(...)):
    req_id = id(file)
    log.info("[req=%s] POST /api/v1/extract file=%s type=%s", req_id, file.filename, file.content_type)

    if file.content_type not in SUPPORTED_TYPES:
        log.warning("[req=%s] Unsupported type: %s", req_id, file.content_type)
        return ExtractionResponse(error=f"Unsupported file type: {file.content_type}")

    file_bytes = await file.read()
    if not file_bytes:
        log.warning("[req=%s] Empty file", req_id)
        return ExtractionResponse(error="Empty file")
    if len(file_bytes) > MAX_FILE_SIZE:
        log.warning("[req=%s] File too large: %d bytes", req_id, len(file_bytes))
        return ExtractionResponse(error="File too large (max 50 MB)")

    from app.logger import Timer
    with Timer(f"[req={req_id}] ocr"):
        try:
            raw_text = extract_text(file_bytes, file.filename or "upload")
        except Exception as e:
            log.error("[req=%s] OCR failed: %s", req_id, e)
            return ExtractionResponse(error=f"OCR failed: {e}")

    if not raw_text.strip():
        log.warning("[req=%s] No text extracted from document", req_id)
        return ExtractionResponse(raw_text=raw_text, error="No text extracted from document")

    with Timer(f"[req={req_id}] llm"):
        try:
            fields = extract_invoice_fields(raw_text)
        except Exception as e:
            log.error("[req=%s] LLM extraction failed: %s", req_id, e)
            return ExtractionResponse(raw_text=raw_text, error=f"LLM extraction failed: {e}")

    raw_containers = fields.get("containers") or fields.get("container_number")
    containers = _normalise_containers(raw_containers)
    container_list = (
        [ContainerInfo(number=c["number"], type_size=c.get("type_size")) for c in containers]
        if containers
        else None
    )

    log.info(
        "[req=%s] Done depot=%s containers=%s",
        req_id, fields.get("depot"),
        [c.number for c in container_list] if container_list else None,
    )
    return ExtractionResponse(
        depot=fields.get("depot"),
        validity_date=fields.get("validity_date"),
        shipping_line=fields.get("shipping_line"),
        containers=container_list,
        raw_text=raw_text,
    )
