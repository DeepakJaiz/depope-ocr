import uuid
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from app.models import OcrResponse, OcrPageResult, ErrorResponse
from app.ocr import ocr_pdf_from_bytes
from app.parser import parse_invoice

app = FastAPI(
    title="Depope OCR",
    description="PDF OCR extraction service — upload a PDF, get text and structured invoice data back.",
    version="1.0.0",
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024


@app.post(
    "/ocr",
    response_model=OcrResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Extract text from a PDF",
    description="Upload a PDF file. Returns raw OCR text per page, combined full text, and structured invoice fields if detected.",
)
async def ocr_pdf_endpoint(file: UploadFile = File(...)) -> OcrResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    try:
        page_texts, full_text = ocr_pdf_from_bytes(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

    pages = [
        OcrPageResult(page_number=i + 1, raw_text=text)
        for i, text in enumerate(page_texts)
    ]

    invoice = parse_invoice(full_text)

    return OcrResponse(
        filename=file.filename,
        total_pages=len(pages),
        full_text=full_text,
        pages=pages,
        invoice=invoice,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
