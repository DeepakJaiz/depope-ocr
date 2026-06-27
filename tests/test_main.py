from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_ocr_non_pdf(client):
    resp = await client.post("/ocr", files={"file": ("test.txt", b"hello", "text/plain")})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Only PDF files are accepted"


@pytest.mark.asyncio
async def test_ocr_no_filename(client):
    resp = await client.post("/ocr", files={"file": ("", b"%PDF-data", "application/pdf")})
    assert resp.status_code in (400, 422)


@pytest.mark.asyncio
async def test_ocr_empty_file(client):
    resp = await client.post("/ocr", files={"file": ("test.pdf", b"", "application/pdf")})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Empty file"


@pytest.mark.asyncio
async def test_ocr_oversized_file(client):
    big = b"x" * (51 * 1024 * 1024)
    resp = await client.post("/ocr", files={"file": ("test.pdf", big, "application/pdf")})
    assert resp.status_code == 413
    assert "too large" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_ocr_processing_error(client):
    big = b"x" * 1024
    with patch("app.main.ocr_pdf_from_bytes", side_effect=RuntimeError("poppler crash")):
        resp = await client.post("/ocr", files={"file": ("test.pdf", big, "application/pdf")})
    assert resp.status_code == 500
    assert "OCR processing failed" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_ocr_success(client, sample_pdf_bytes):
    resp = await client.post(
        "/ocr",
        files={"file": ("invoice.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "invoice.pdf"
    assert data["total_pages"] >= 1
    assert len(data["full_text"]) > 0
    assert len(data["pages"]) == data["total_pages"]
    assert data["pages"][0]["page_number"] == 1
    assert data["invoice"] is not None
