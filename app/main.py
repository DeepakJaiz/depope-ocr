from fastapi import FastAPI

from app.logger import log
from app.router import router
from app.schemas import HealthResponse

app = FastAPI(
    title="Depope OCR",
    description="Upload scanned PDFs/images → OCR → LLM extraction → structured invoice fields",
    version="1.0.0",
)
app.include_router(router, prefix="/api/v1")


@app.get("/health", response_model=HealthResponse)
async def health():
    onnx_ok = None
    try:
        import onnxruntime
        onnx_ok = onnxruntime.__version__
        log.info("onnxruntime %s detected", onnx_ok)
    except ImportError:
        log.warning("onnxruntime not installed — OCR will be slower")

    ocr_loaded = False
    try:
        from app.ocr import get_ocr
        get_ocr()
        ocr_loaded = True
    except Exception as e:
        log.error("OCR model load failed: %s", e)

    return HealthResponse(
        status="ok",
        onnxruntime_version=onnx_ok,
        ocr_loaded=ocr_loaded,
    )
