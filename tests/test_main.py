from unittest.mock import patch, MagicMock, PropertyMock

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "ocr_loaded" in data


@pytest.mark.asyncio
async def test_extract_unsupported_type(client):
    resp = await client.post("/api/v1/extract", files={"file": ("test.txt", b"hello", "text/plain")})
    assert resp.status_code == 200
    assert resp.json()["error"] == "Unsupported file type: text/plain"


@pytest.mark.asyncio
async def test_extract_empty_file(client):
    resp = await client.post("/api/v1/extract", files={"file": ("test.pdf", b"", "application/pdf")})
    assert resp.status_code == 200
    assert resp.json()["error"] == "Empty file"


@pytest.mark.asyncio
async def test_extract_success(client, sample_pdf_bytes):
    with (
        patch("app.main.extract_text", return_value="OCR text with containers FFAU6029848"),
        patch("app.main.extract_invoice_fields") as mock_llm,
    ):
        mock_llm.return_value = {
            "depot": "DP World Nhava Sheva",
            "validity_date": "25-Jul-2026",
            "shipping_line": "MAERSK",
            "containers": [
                {"number": "FFAU6029848", "type_size": "20' DV"},
                {"number": "HASU1493470", "type_size": "40' HC"},
            ],
        }
        resp = await client.post(
            "/api/v1/extract",
            files={"file": ("invoice.pdf", sample_pdf_bytes, "application/pdf")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["depot"] == "DP World Nhava Sheva"
    assert data["validity_date"] == "25-Jul-2026"
    assert data["shipping_line"] == "MAERSK"
    assert len(data["containers"]) == 2
    assert data["containers"][0]["number"] == "FFAU6029848"
    assert data["containers"][0]["type_size"] == "20' DV"
    assert data["containers"][1]["number"] == "HASU1493470"
    assert data["containers"][1]["type_size"] == "40' HC"
    assert data["raw_text"] is not None
    assert data["error"] is None


@pytest.mark.asyncio
async def test_extract_ocr_failure(client):
    with patch("app.main.extract_text", side_effect=RuntimeError("poppler crash")):
        resp = await client.post(
            "/api/v1/extract",
            files={"file": ("test.pdf", b"x" * 1024, "application/pdf")},
        )
    assert resp.status_code == 200
    assert "OCR failed" in resp.json()["error"]


@pytest.mark.asyncio
async def test_extract_llm_failure(client):
    with (
        patch("app.main.extract_text", return_value="some OCR text"),
        patch("app.main.extract_invoice_fields", side_effect=RuntimeError("LLM error")),
    ):
        resp = await client.post(
            "/api/v1/extract",
            files={"file": ("test.pdf", b"x" * 1024, "application/pdf")},
        )
    assert resp.status_code == 200
    assert "LLM extraction failed" in resp.json()["error"]
    assert resp.json()["raw_text"] is not None
