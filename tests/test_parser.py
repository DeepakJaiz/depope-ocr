import pytest
from app.models import ExtractedInvoice
from app.parser import parse_invoice, _parse_float


class TestParseFloat:
    def test_none(self):
        assert _parse_float(None) is None

    def test_invalid(self):
        assert _parse_float("abc") is None

    def test_integer_string(self):
        assert _parse_float("42") == 42.0

    def test_with_comma(self):
        assert _parse_float("1,234.56") == 1234.56

    def test_currency_symbol(self):
        assert _parse_float("$100") is None  # dollar sign not stripped


class TestParseInvoiceFull:
    def test_all_fields(self):
        text = (
            "INVOICE #INV-001\n"
            "Date: 2024-06-01\n"
            "Vendor: Acme Corp\n"
            "Widget A  2  $10.00  $20.00\n"
            "Widget B  1  $15.00  $15.00\n"
            "Subtotal: $35.00\n"
            "Tax: $3.50\n"
            "Grand Total: $38.50\n"
        )
        inv = parse_invoice(text)
        assert inv.invoice_number == "INV-001"
        assert inv.date == "2024-06-01"
        assert inv.vendor_name == "Acme Corp"
        assert inv.subtotal == 35.0
        assert inv.tax == 3.5
        assert inv.total == 38.5
        assert len(inv.line_items) == 2
        assert inv.line_items[0].description == "Widget A"
        assert inv.line_items[0].quantity == 2
        assert inv.line_items[0].unit_price == 10.0
        assert inv.line_items[0].total == 20.0
        assert inv.line_items[1].description == "Widget B"

    def test_no_matches(self):
        inv = parse_invoice("random text with no invoice fields")
        assert inv.invoice_number is None
        assert inv.date is None
        assert inv.vendor_name is None
        assert inv.subtotal is None
        assert inv.tax is None
        assert inv.total is None
        assert inv.line_items == []

    def test_empty_string(self):
        inv = parse_invoice("")
        assert inv.invoice_number is None
        assert inv.line_items == []


class TestParseInvoiceNumber:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Invoice No: ABC-123", "ABC-123"),
            ("Invoice # 456", "456"),
            ("INV-789", "INV-789"),
            ("invoice number 001", "001"),
            ("Invoice Num 999", "999"),
        ],
    )
    def test_variants(self, text, expected):
        assert parse_invoice(text).invoice_number == expected

    def test_no_match(self):
        assert parse_invoice("no invoice ref here").invoice_number is None


class TestParseDate:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Date: 2024-06-01", "2024-06-01"),
            ("Invoice Date 01/15/2024", "01/15/2024"),
            ("2024-06-01", "2024-06-01"),
        ],
    )
    def test_variants(self, text, expected):
        assert parse_invoice(text).date == expected


class TestParseVendor:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Vendor: Mega Supplies", "Mega Supplies"),
            ("Seller: Corner Shop", "Corner Shop"),
            ("From: Wholesale Inc.", "Wholesale Inc."),
            ("Bill From: XYZ Corp", "XYZ Corp"),
        ],
    )
    def test_variants(self, text, expected):
        assert parse_invoice(text).vendor_name == expected


class TestParseTotals:
    def test_total_variants(self):
        assert parse_invoice("Total: $100.00").total == 100.0
        assert parse_invoice("Amount Due: $200.00").total == 200.0
        assert parse_invoice("Grand Total $300.00").total == 300.0

    def test_subtotal(self):
        assert parse_invoice("Subtotal: $50.00").subtotal == 50.0
        assert parse_invoice("Sub Total: $75.00").subtotal == 75.0

    def test_tax_variants(self):
        assert parse_invoice("Tax: $10.00").tax == 10.0
        assert parse_invoice("VAT: $20.00").tax == 20.0
        assert parse_invoice("GST $30.00").tax == 30.0

    def test_with_currency_symbols(self):
        assert parse_invoice("Total: €100.00").total == 100.0
        assert parse_invoice("Total: £100.00").total == 100.0
        assert parse_invoice("Total: ₹100.00").total == 100.0

    def test_no_totals(self):
        inv = parse_invoice("some random text")
        assert inv.total is None
        assert inv.subtotal is None
        assert inv.tax is None


class TestParseLineItems:
    def test_multiple_items(self):
        text = "Item A  3  $5.00  $15.00\nItem B  2  $10.00  $20.00\n"
        inv = parse_invoice(text)
        assert len(inv.line_items) == 2

    def test_item_format(self):
        text = "Product X  1  $99.99  $99.99\n"
        inv = parse_invoice(text)
        assert inv.line_items[0].description == "Product X"
        assert inv.line_items[0].quantity == 1
        assert inv.line_items[0].unit_price == 99.99
        assert inv.line_items[0].total == 99.99

    def test_no_items(self):
        assert parse_invoice("no line items here").line_items == []
