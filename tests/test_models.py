from app.models import (
    ExtractedLineItem,
    ExtractedInvoice,
    OcrPageResult,
    OcrResponse,
    ErrorResponse,
)


class TestExtractedLineItem:
    def test_defaults(self):
        item = ExtractedLineItem()
        assert item.description is None
        assert item.quantity is None
        assert item.unit_price is None
        assert item.total is None

    def test_full(self):
        item = ExtractedLineItem(
            description="Widget", quantity=2, unit_price=10.0, total=20.0
        )
        assert item.description == "Widget"
        assert item.quantity == 2
        assert item.unit_price == 10.0
        assert item.total == 20.0


class TestExtractedInvoice:
    def test_defaults(self):
        inv = ExtractedInvoice()
        assert inv.invoice_number is None
        assert inv.date is None
        assert inv.vendor_name is None
        assert inv.line_items == []

    def test_with_items(self):
        inv = ExtractedInvoice(
            invoice_number="INV-001",
            date="2024-01-01",
            vendor_name="Test Vendor",
            total=100.0,
            line_items=[ExtractedLineItem(description="A", quantity=1, unit_price=50.0, total=50.0)],
        )
        assert inv.invoice_number == "INV-001"
        assert len(inv.line_items) == 1


class TestOcrPageResult:
    def test_fields(self):
        p = OcrPageResult(page_number=1, raw_text="hello")
        assert p.page_number == 1
        assert p.raw_text == "hello"


class TestOcrResponse:
    def test_full(self):
        r = OcrResponse(
            filename="test.pdf",
            total_pages=1,
            full_text="hello",
            pages=[OcrPageResult(page_number=1, raw_text="hello")],
            invoice=ExtractedInvoice(invoice_number="INV-001"),
        )
        assert r.filename == "test.pdf"
        assert r.invoice is not None
        assert r.invoice.invoice_number == "INV-001"

    def test_no_invoice(self):
        r = OcrResponse(
            filename="test.pdf", total_pages=1, full_text="", pages=[]
        )
        assert r.invoice is None


class TestErrorResponse:
    def test_minimal(self):
        e = ErrorResponse(error="bad")
        assert e.error == "bad"
        assert e.detail is None

    def test_full(self):
        e = ErrorResponse(error="bad", detail="something broke")
        assert e.detail == "something broke"
